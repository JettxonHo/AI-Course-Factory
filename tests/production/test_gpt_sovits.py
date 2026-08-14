"""Public behavior tests for the explicit local GPT-SoVITS voice adapter."""

from pathlib import Path
from dataclasses import replace
import os
import subprocess
from tempfile import TemporaryDirectory
import unittest
import wave
from unittest.mock import patch

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference, WorkspaceFailure
from ai_course_factory.production import (
    GPT_SOVITS_GPT_MODEL_BASENAME,
    GPT_SOVITS_MODEL_IDENTIFIER,
    GPT_SOVITS_SOVITS_MODEL_BASENAME,
    GPTSoVITSConfiguration,
    GPTSoVITSSyntheticVoiceGenerator,
    LocalNarrationRenderer,
    LocalNarrationPreflight,
    LocalNarrationTask,
    LocalNarrationResult,
    MediaGenerationResult,
    ProductionMediaFailure,
    VoiceGenerator,
    VoiceSynthesisTask,
)


def _fixture_runtime(root: Path) -> tuple[Path, Path, Path, GPTSoVITSConfiguration]:
    repo = root / "repo"
    (repo / "GPT_SoVITS" / "configs").mkdir(parents=True)
    (repo / ".git").mkdir()
    executable = root / "python311"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    gpt_dir = repo / "GPT_SoVITS" / "pretrained_models" / GPT_SOVITS_MODEL_IDENTIFIER
    gpt_dir.mkdir(parents=True)
    for path in (
        repo / "GPT_SoVITS" / "inference_cli.py",
        gpt_dir / GPT_SOVITS_GPT_MODEL_BASENAME,
        gpt_dir / GPT_SOVITS_SOVITS_MODEL_BASENAME,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    (repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml").write_text(
        "version: v2\nt2s_weights_path: s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt\nvits_weights_path: s2G2333k.pth\n",
        encoding="utf-8",
    )
    for model_dir in ("chinese-roberta-wwm-ext-large", "chinese-hubert-base"):
        (repo / "GPT_SoVITS" / "pretrained_models" / model_dir).mkdir(parents=True)
    g2pw = repo / "GPT_SoVITS" / "text" / "G2PWModel"
    g2pw.mkdir(parents=True)
    for name in (
        "config.py",
        "g2pW.onnx",
        "bopomofo_to_pinyin_wo_tune_dict.json",
        "char_bopomofo_dict.json",
        "POLYPHONIC_CHARS.txt",
        "MONOPHONIC_CHARS.txt",
    ):
        (g2pw / name).write_bytes(b"fixture")
    reference = root / "reference.wav"
    with wave.open(str(reference), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\0\0" * 2400)
    config = GPTSoVITSConfiguration(
        external_python=str(executable),
        repository_root=str(repo),
        repository_commit="d523079fc05d9a8028d6085bffe4a2757c32abb6",
        inference_script=str(repo / "GPT_SoVITS" / "inference_cli.py"),
        tts_config=str(repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml"),
        gpt_model=str(gpt_dir / GPT_SOVITS_GPT_MODEL_BASENAME),
        sovits_model=str(gpt_dir / GPT_SOVITS_SOVITS_MODEL_BASENAME),
        reference_audio=str(reference),
    )
    return repo, executable, reference, config


class GPTSoVITSSmokeAdapterTests(unittest.TestCase):
    def test_preflight_failure_can_retry_after_runtime_boundary_is_repaired(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _repo, executable, _reference, config = _fixture_runtime(root)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:handoff-preflight-retry")
            repaired = False
            calls = []

            def runner(argv, **kwargs):
                calls.append(argv)
                if argv[0] == str(executable) and argv[1] == "--version":
                    if not repaired:
                        return subprocess.CompletedProcess(argv, 1, b"", b"runtime unavailable")
                    return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                if argv[0] == str(executable) and argv[1] == "-c":
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, b"d523079fc05d9a8028d6085bffe4a2757c32abb6\n", b"")
                return subprocess.run(argv, **kwargs)

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            first = adapter.preflight()
            self.assertIsInstance(first, ProductionMediaFailure)
            self.assertEqual(first.code, "GPT_SOVITS_PYTHON_UNAVAILABLE")
            repaired = True
            second = adapter.preflight()
            self.assertIsInstance(second, LocalNarrationPreflight)
            self.assertEqual(sum(1 for argv in calls if len(argv) > 1 and argv[1] == "--version"), 2)

    def test_local_narration_renderer_reuses_validated_runtime_across_scenes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, _reference, config = _fixture_runtime(root)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:handoff")
            calls = []

            def runner(argv, **kwargs):
                calls.append(argv)
                if argv[0] == str(executable) and argv[1] == "--version":
                    return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                if argv[0] == str(executable) and argv[1] == "-c":
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, b"d523079fc05d9a8028d6085bffe4a2757c32abb6\n", b"")
                if argv[0] == str(executable):
                    output = Path(argv[argv.index("--output_path") + 1]) / "output.wav"
                    with wave.open(str(output), "wb") as handle:
                        handle.setnchannels(1)
                        handle.setsampwidth(2)
                        handle.setframerate(24000)
                        handle.writeframes(b"\0\0" * 2400)
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                return subprocess.run(argv, **kwargs)

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            self.assertIsInstance(adapter, LocalNarrationRenderer)
            for index in range(1, 3):
                task = LocalNarrationTask(
                    "task:handoff", ArtifactReference("production_request", "episode-1", 1), f"scene-{index}",
                    "Simplified Chinese", 1.0, "你好。", WorkspaceFileReference("task:handoff", "media", f"handoff-narration-scene-{index}.m4a"),
                )
                result = adapter.render(task)
                self.assertIsInstance(result, LocalNarrationResult)
            self.assertEqual(sum(1 for argv in calls if len(argv) > 1 and argv[1] == "--version"), 1)
            self.assertEqual(sum(1 for argv in calls if len(argv) > 1 and argv[1] == "-c"), 1)
            self.assertEqual(sum(1 for argv in calls if argv and argv[0] == "git"), 1)
    def test_fake_cli_generates_zero_charge_normalized_audio_through_voice_seam(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, reference, config = _fixture_runtime(root)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits")
            task = VoiceSynthesisTask(
                "task:gpt-sovits",
                "attempt:voice:1",
                ArtifactReference("production_request", "episode-1", 1),
                "scene-1",
                "Simplified Chinese",
                1.0,
                "你好。",
                WorkspaceFileReference("task:gpt-sovits", "media", "scene-1.m4a"),
            )
            calls = []
            inference_cwds: list[Path] = []

            def runner(argv, **kwargs):
                calls.append((argv, kwargs))
                if argv[0] == str(executable) and argv[1] == "--version":
                    return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                if argv[0] == str(executable) and argv[1] == "-c":
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, b"d523079fc05d9a8028d6085bffe4a2757c32abb6\n", b"")
                if argv[0] == str(executable):
                    inference_cwds.append(Path(kwargs["cwd"]))
                    self.assertNotEqual(inference_cwds[-1], repo.resolve())
                    self.assertTrue((inference_cwds[-1] / "GPT_SoVITS").is_symlink())
                    child_env = kwargs["env"]
                    self.assertNotIn("ACF_SENTINEL_SECRET", child_env)
                    self.assertNotIn("VIRTUAL_ENV", child_env)
                    self.assertNotIn("project-secret", child_env.get("PYTHONPATH", ""))
                    output = Path(argv[argv.index("--output_path") + 1]) / "output.wav"
                    with wave.open(str(output), "wb") as handle:
                        handle.setnchannels(1)
                        handle.setsampwidth(2)
                        handle.setframerate(24000)
                        handle.writeframes(b"\0\0" * 2400)
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                return subprocess.run(argv, **kwargs)

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            self.assertIsInstance(adapter, VoiceGenerator)
            with patch.dict(os.environ, {"ACF_SENTINEL_SECRET": "do-not-forward", "PYTHONPATH": "project-secret", "VIRTUAL_ENV": "/project/.venv"}):
                result = adapter.synthesize(task)
            self.assertIsInstance(result, MediaGenerationResult)
            self.assertEqual(result.provider, "local-gpt-sovits-v2")
            self.assertEqual(result.media_type, "audio/mp4")
            self.assertEqual(result.result_code, "SUCCESS")
            inference_calls = [item for item in calls if "--gpt_model" in item[0]]
            self.assertEqual(len(inference_calls), 1)
            self.assertEqual(inference_calls[0][1]["shell"], False)
            self.assertEqual(inference_calls[0][0][inference_calls[0][0].index("--ref_text") + 1].endswith("reference.txt"), True)
            self.assertEqual(inference_calls[0][0][inference_calls[0][0].index("--target_text") + 1].endswith("target.txt"), True)
            self.assertEqual(calls[-1][1]["shell"], False)
            self.assertEqual(len(inference_cwds), 1)
            self.assertFalse((repo / "weight.json").exists())

    def test_invalid_preflight_has_no_runner_or_workspace_side_effect(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-invalid")
            config = GPTSoVITSConfiguration(
                external_python=str(root / "missing-python"),
                repository_root=str(root / "missing-repo"),
                repository_commit="d523079fc05d9a8028d6085bffe4a2757c32abb6",
                inference_script=str(root / "missing-cli.py"),
                tts_config=str(root / "missing.yaml"),
                gpt_model=str(root / "missing.ckpt"),
                sovits_model=str(root / "missing.pth"),
                reference_audio=str(root / "missing.wav"),
            )
            calls = []

            def runner(argv, **kwargs):
                calls.append((argv, kwargs))
                return subprocess.CompletedProcess(argv, 1, b"", b"")

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            result = adapter.preflight()

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GPT_SOVITS_CONFIG_INVALID")
            self.assertEqual(calls, [])
            self.assertIsInstance(
                workspace.read(WorkspaceFileReference("task:gpt-sovits-invalid", "media", "scene-1.m4a")),
                WorkspaceFailure,
            )

    def test_missing_g2pw_asset_fails_before_runtime_probe_or_workspace_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, _reference, config = _fixture_runtime(root)
            (repo / "GPT_SoVITS" / "text" / "G2PWModel" / "g2pW.onnx").unlink()
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-g2pw")
            calls = []

            def runner(argv, **kwargs):
                calls.append((argv, kwargs))
                return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            result = adapter.preflight()

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GPT_SOVITS_CONFIG_INVALID")
            self.assertEqual(calls, [])
            self.assertIsInstance(
                workspace.read(WorkspaceFileReference("task:gpt-sovits-g2pw", "media", "scene-1.m4a")),
                WorkspaceFailure,
            )

    def test_mislabeled_model_identifier_fails_before_runtime_probe_or_workspace_write(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            _repo, _executable, _reference, valid = _fixture_runtime(root)
            config = replace(valid, model_identifier="another-v2-model")
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-model-id")
            calls = []

            def runner(argv, **kwargs):
                calls.append((argv, kwargs))
                return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")

            adapter = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner)
            result = adapter.preflight()

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GPT_SOVITS_CONFIG_INVALID")
            self.assertEqual(calls, [])

    def test_symlinked_venv_path_is_invoked_exactly_and_missing_dependency_fails_before_inference(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, _reference, valid = _fixture_runtime(root)
            configured_python = root / "venv" / "bin" / "python"
            configured_python.parent.mkdir(parents=True)
            configured_python.symlink_to(executable)
            config = replace(valid, external_python=str(configured_python))
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-dependency")
            task = VoiceSynthesisTask(
                "task:gpt-sovits-dependency", "attempt:voice:dependency", ArtifactReference("production_request", "episode-1", 1),
                "scene-1", "Simplified Chinese", 1.0, "你好。",
                WorkspaceFileReference("task:gpt-sovits-dependency", "media", "scene-1.m4a"),
            )
            calls = []
            with patch.dict(os.environ, {"ACF_SENTINEL_SECRET": "do-not-forward", "PYTHONPATH": "project-secret", "VIRTUAL_ENV": "/project/.venv"}):
                def runner(argv, **kwargs):
                    calls.append((argv, kwargs))
                    self.assertEqual(argv[0], str(configured_python))
                    child_env = kwargs.get("env", {})
                    self.assertNotIn("ACF_SENTINEL_SECRET", child_env)
                    self.assertNotEqual(child_env.get("PYTHONPATH"), "project-secret")
                    self.assertNotIn("project-secret", child_env.get("PYTHONPATH", ""))
                    self.assertNotIn("VIRTUAL_ENV", child_env)
                    if argv[1] == "--version":
                        return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                    if argv[1] == "-c":
                        return subprocess.CompletedProcess(argv, 1, b"", b"missing soundfile")
                    self.fail("inference was reached before dependency preflight")

                result = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner).synthesize(task)

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GPT_SOVITS_DEPENDENCIES_UNAVAILABLE")
            self.assertEqual(len(calls), 2)
            self.assertIsInstance(workspace.read(task.output_reference), WorkspaceFailure)

    def test_overlong_generated_speech_fails_before_workspace_commit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, reference, config = _fixture_runtime(root)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-overlong")
            task = VoiceSynthesisTask(
                "task:gpt-sovits-overlong", "attempt:voice:overlong", ArtifactReference("production_request", "episode-1", 1),
                "scene-1", "Simplified Chinese", 1.0, "你好。",
                WorkspaceFileReference("task:gpt-sovits-overlong", "media", "scene-1.m4a"),
            )

            def runner(argv, **kwargs):
                if argv[0] == str(executable) and argv[1] == "--version":
                    return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                if argv[0] == str(executable) and argv[1] == "-c":
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, b"d523079fc05d9a8028d6085bffe4a2757c32abb6\n", b"")
                if argv[0] == str(executable):
                    output = Path(argv[argv.index("--output_path") + 1]) / "output.wav"
                    with wave.open(str(output), "wb") as handle:
                        handle.setnchannels(1)
                        handle.setsampwidth(2)
                        handle.setframerate(24000)
                        handle.writeframes(b"\0\0" * 26_400)  # 1.1 seconds, over a 1-second Scene
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                return subprocess.run(argv, **kwargs)

            result = GPTSoVITSSyntheticVoiceGenerator(workspace, config, runner=runner).synthesize(task)

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GPT_SOVITS_AUDIO_INVALID")
            self.assertIsInstance(workspace.read(task.output_reference), WorkspaceFailure)

    def test_existing_bound_output_replays_without_inference_and_conflict_fails_closed(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo, executable, reference, config = _fixture_runtime(root)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:gpt-sovits-replay")
            task = VoiceSynthesisTask(
                "task:gpt-sovits-replay", "attempt:voice:replay", ArtifactReference("production_request", "episode-1", 1),
                "scene-1", "Simplified Chinese", 1.0, "你好。", WorkspaceFileReference("task:gpt-sovits-replay", "media", "scene-1.m4a"),
            )
            inference_calls = []

            class CorruptibleWorkspace:
                def __init__(self, delegate):
                    self.delegate = delegate
                    self.corrupt = False

                def prepare(self, task_id):
                    return self.delegate.prepare(task_id)

                def commit(self, reference, content):
                    return self.delegate.commit(reference, content)

                def read(self, reference):
                    return b"not-audio" if self.corrupt else self.delegate.read(reference)

            proxy = CorruptibleWorkspace(workspace)

            def runner(argv, **kwargs):
                if argv[0] == str(executable) and argv[1] == "--version":
                    return subprocess.CompletedProcess(argv, 0, b"Python 3.11.15\n", b"")
                if argv[0] == str(executable) and argv[1] == "-c":
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                if argv[0] == "git":
                    return subprocess.CompletedProcess(argv, 0, b"d523079fc05d9a8028d6085bffe4a2757c32abb6\n", b"")
                if argv[0] == str(executable):
                    inference_calls.append(argv)
                    output = Path(argv[argv.index("--output_path") + 1]) / "output.wav"
                    with wave.open(str(output), "wb") as handle:
                        handle.setnchannels(1); handle.setsampwidth(2); handle.setframerate(24000); handle.writeframes(b"\0\0" * 2400)
                    return subprocess.CompletedProcess(argv, 0, b"", b"")
                return subprocess.run(argv, **kwargs)

            adapter = GPTSoVITSSyntheticVoiceGenerator(proxy, config, runner=runner)
            first = adapter.synthesize(task)
            replay = adapter.synthesize(task)
            self.assertIsInstance(first, MediaGenerationResult)
            self.assertIsInstance(replay, MediaGenerationResult)
            self.assertEqual(len(inference_calls), 1)

            proxy.corrupt = True
            conflict = adapter.synthesize(task)
            self.assertIsInstance(conflict, ProductionMediaFailure)
            self.assertEqual(conflict.code, "MEDIA_OUTPUT_CONFLICT")


if __name__ == "__main__":
    unittest.main()
