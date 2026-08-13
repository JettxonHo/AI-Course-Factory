"""Durable local GPT-SoVITS path with a controlled CLI and real FFmpeg."""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
import wave
from unittest.mock import patch
import zipfile

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.persistence import WorkspaceFileReference, WorkspaceFailure
from ai_course_factory.production import (
    GPT_SOVITS_GPT_MODEL_BASENAME,
    GPT_SOVITS_MODEL_IDENTIFIER,
    GPT_SOVITS_PROVIDER,
    GPT_SOVITS_SOVITS_MODEL_BASENAME,
    GPTSoVITSConfiguration,
    ProviderAttemptRecord,
)


COMMIT = "d523079fc05d9a8028d6085bffe4a2757c32abb6"
TRANSCRIPT = "你好，我是小土豆。今天我们一起认识人工智能。"


def _tool(name: str, fallback: str) -> str:
    return shutil.which(name) or fallback


def _write_png(path: Path, colour: str) -> None:
    subprocess.run(
        [
            _tool("ffmpeg", "/opt/homebrew/bin/ffmpeg"),
            "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
            "-i", f"color=c={colour}:s=32x32", "-frames:v", "1", str(path),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _fixture_runtime(root: Path) -> tuple[GPTSoVITSConfiguration, Path, Path]:
    """Create text-only fake runtime files; generated narration uses FFmpeg."""

    repo = root / "repo"
    (repo / "GPT_SoVITS" / "configs").mkdir(parents=True)
    (repo / ".git").mkdir()
    model_dir = repo / "GPT_SoVITS" / "pretrained_models" / GPT_SOVITS_MODEL_IDENTIFIER
    model_dir.mkdir(parents=True)
    for path in (
        repo / "GPT_SoVITS" / "inference_cli.py",
        model_dir / GPT_SOVITS_GPT_MODEL_BASENAME,
        model_dir / GPT_SOVITS_SOVITS_MODEL_BASENAME,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    (repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml").write_text(
        "version: v2\nt2s_weights_path: s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt\n"
        "vits_weights_path: s2G2333k.pth\n",
        encoding="utf-8",
    )
    for name in ("chinese-roberta-wwm-ext-large", "chinese-hubert-base"):
        (repo / "GPT_SoVITS" / "pretrained_models" / name).mkdir(parents=True)
    g2pw = repo / "GPT_SoVITS" / "text" / "G2PWModel"
    g2pw.mkdir(parents=True)
    for name in (
        "config.py", "g2pW.onnx", "bopomofo_to_pinyin_wo_tune_dict.json",
        "char_bopomofo_dict.json", "POLYPHONIC_CHARS.txt", "MONOPHONIC_CHARS.txt",
    ):
        (g2pw / name).write_bytes(b"fixture")

    reference = root / "reference.wav"
    with wave.open(str(reference), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\0\0" * 2400)

    log = root / "inference.log"
    executable = root / "python311-fixture"
    ffmpeg = _tool("ffmpeg", "/opt/homebrew/bin/ffmpeg")
    executable.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Python 3.11.15'; exit 0; fi\n"
        "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
        f"echo inference >> {shlex.quote(str(log))}\n"
        "out=''\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--output_path\" ]; then out=\"$2\"; shift 2; else shift; fi\n"
        "done\n"
        "mkdir -p \"$out\"\n"
        f"{shlex.quote(ffmpeg)} -hide_banner -loglevel error -y -f lavfi -i sine=frequency=880:duration=1 "
        "-ar 24000 -ac 1 \"$out/output.wav\"\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)

    config = GPTSoVITSConfiguration(
        external_python=str(executable),
        repository_root=str(repo),
        repository_commit=COMMIT,
        inference_script=str(repo / "GPT_SoVITS" / "inference_cli.py"),
        tts_config=str(repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml"),
        gpt_model=str(model_dir / GPT_SOVITS_GPT_MODEL_BASENAME),
        sovits_model=str(model_dir / GPT_SOVITS_SOVITS_MODEL_BASENAME),
        reference_audio=str(reference),
        reference_transcript=TRANSCRIPT,
    )

    fake_bin = root / "fake-bin"
    fake_bin.mkdir()
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"-C\" ] && [ \"$3\" = \"rev-parse\" ]; then\n"
        f"  echo {COMMIT}\n"
        "  exit 0\n"
        "fi\nexit 1\n",
        encoding="utf-8",
    )
    fake_git.chmod(0o755)
    return config, log, fake_bin


class GPTSoVITSLocalIntegrationTests(unittest.TestCase):
    def _advance_to_production(self, app: CourseFactoryApplication) -> None:
        self.assertEqual(app.create_or_open().status, "success")
        self.assertEqual(app.submit_script_decision("approve").status, "success")
        self.assertEqual(app.advance_planning().status, "success")
        self.assertEqual(app.submit_budget_decision("approve").status, "success")

    def test_restart_without_explicit_runtime_does_not_silently_replay_as_fixture(self):
        config = GPTSoVITSConfiguration(
            external_python="/missing/python311",
            repository_root="/missing/gpt-sovits-repo",
            repository_commit=COMMIT,
            inference_script="/missing/inference_cli.py",
            tts_config="/missing/tts_infer.yaml",
            gpt_model="/missing/gpt.ckpt",
            sovits_model="/missing/sovits.pth",
            reference_audio="/missing/reference.wav",
        )
        with TemporaryDirectory() as directory:
            app = CourseFactoryApplication(Path(directory), tts_configuration=config)
            self._advance_to_production(app)
            failed = app.produce_offline()
            self.assertEqual(failed.error_code, "GPT_SOVITS_CONFIG_INVALID")
            self.assertEqual(failed.view.provider_attempt_count, 0)
            app.close()

            resumed = CourseFactoryApplication(Path(directory))
            replay = resumed.create_or_open()
            self.assertEqual(replay.view.stage, "production")
            self.assertEqual(replay.view.provider_attempt_count, 0)
            self.assertEqual(replay.view.tts_engine, "local-gpt-sovits-v2")
            self.assertEqual(resumed.produce_offline().error_code, "GPT_SOVITS_CONFIG_REQUIRED")

    def test_imported_gpt_sovits_production_replacement_restart_and_package_are_durable(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            for index, colour in enumerate(("red", "blue", "green", "yellow", "purple", "orange"), start=1):
                _write_png(imports / f"scene-{index}.png", colour)
            config, inference_log, fake_bin = _fixture_runtime(root)
            original_path = os.environ.get("PATH", "")
            with patch.dict(os.environ, {"PATH": f"{fake_bin}{os.pathsep}{original_path}"}):
                app = CourseFactoryApplication(root / "data", visual_import_dir=imports, tts_configuration=config)
                self._advance_to_production(app)

                produced = app.produce_offline()
                self.assertEqual(produced.status, "success")
                self.assertEqual(produced.view.provider_attempt_count, 12)
                self.assertEqual(inference_log.read_text(encoding="utf-8").splitlines(), ["inference"] * 6)

                state_before = app._load_state()
                self.assertIsNotNone(state_before)
                composition_before = state_before.composition
                self.assertIsNotNone(composition_before)
                voice_payloads = tuple(scene["voice_result"] for scene in composition_before["scenes"])
                self.assertTrue(all(item["provider"] == GPT_SOVITS_PROVIDER for item in voice_payloads))
                self.assertTrue(all(item["output_reference"]["name"].endswith(".m4a") for item in voice_payloads))
                records = app.attempts.list_for_authorization(state_before.authorization_id)
                self.assertIsInstance(records, tuple)
                voice_records = tuple(item for item in records if isinstance(item, ProviderAttemptRecord) and item.operation == "voice")
                self.assertEqual(len(voice_records), 6)
                self.assertTrue(all(item.provider == GPT_SOVITS_PROVIDER and item.charged_amount_micros == 0 for item in voice_records))
                before_voice_files = {
                    item["output_reference"]["name"]: app.workspace.read(
                        WorkspaceFileReference(**item["output_reference"])
                    )
                    for item in voice_payloads
                }
                before_audio_refs = composition_before["scene_audio_references"]
                before_master_audio = composition_before["master_audio_reference"]
                before_clips = composition_before["scene_clip_references"]

                _write_png(imports / "scene-2-replacement.png", "pink")
                replaced = app.replace_scene("scene-2")
                self.assertEqual(replaced.status, "success")
                state_after = app._load_state()
                self.assertIsNotNone(state_after)
                composition_after = state_after.composition
                self.assertIsNotNone(composition_after)
                self.assertEqual(composition_after["scenes"][1]["voice_result"], voice_payloads[1])
                self.assertEqual(composition_after["scene_audio_references"], before_audio_refs)
                self.assertEqual(composition_after["master_audio_reference"], before_master_audio)
                self.assertEqual(tuple(composition_after["scene_clip_references"][index] for index in (0, 2, 3, 4, 5)), tuple(before_clips[index] for index in (0, 2, 3, 4, 5)))
                self.assertEqual(inference_log.read_text(encoding="utf-8").splitlines(), ["inference"] * 6)
                records_after = app.attempts.list_for_authorization(state_after.authorization_id)
                self.assertEqual(len(records_after), len(records))
                for name, content in before_voice_files.items():
                    self.assertEqual(app.workspace.read(WorkspaceFileReference("demo-episode-01", "media", name)), content)

                replacement_video = replaced.view.video_reference
                app.close()
                resumed = CourseFactoryApplication(root / "data", visual_import_dir=imports, tts_configuration=config)
                self.assertEqual(resumed.create_or_open().view.video_reference, replacement_video)
                self.assertEqual(resumed.produce_offline().status, "success")
                self.assertEqual(inference_log.read_text(encoding="utf-8").splitlines(), ["inference"] * 6)
                self.assertEqual(resumed.submit_final_decision("approve").status, "success")
                exported = resumed.export_package()
                self.assertEqual(exported.status, "success")
                package_bytes = resumed.workspace.read(exported.view.package_output)
                self.assertIsInstance(package_bytes, bytes)
                with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
                    attribution = json.loads(archive.read("source-attribution.json"))
                self.assertEqual(attribution["repository_url"], "https://github.com/microsoft/AI-For-Beginners")
                self.assertTrue(attribution["units"])
                self.assertTrue(attribution["visual_assets"])
                self.assertEqual(attribution["tts"]["engine"], GPT_SOVITS_PROVIDER)
                self.assertEqual(attribution["tts"]["reference_provenance"], "locally generated Qwen3-TTS Serena synthetic reference")
                self.assertFalse(attribution["tts"]["application_provider_api_call"])
                self.assertEqual(attribution["tts"]["external_charge_micros"], 0)
                resumed.close()

                replayed = CourseFactoryApplication(root / "data", visual_import_dir=imports, tts_configuration=config)
                self.assertEqual(replayed.create_or_open().view.stage, "exported")
                self.assertEqual(replayed.workspace.read(exported.view.package_output), package_bytes)
                self.assertEqual(inference_log.read_text(encoding="utf-8").splitlines(), ["inference"] * 6)
                replayed.close()


if __name__ == "__main__":
    unittest.main()
