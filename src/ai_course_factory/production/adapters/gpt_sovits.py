"""Explicit local GPT-SoVITS v2 voice adapter.

The adapter deliberately owns the external-runtime boundary.  The application
passes an operator configuration for a Python 3.11 environment, an official
GPT-SoVITS checkout and its model/reference files.  Inference is a one-shot
argv invocation of the repository's CLI; no WebUI/API process is started and
no network or credential is involved here.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from typing import Any, Callable, Mapping

from ai_course_factory.persistence import WorkspaceAdapter, WorkspaceFileReference, WorkspaceFileRecord, WorkspaceFailure

from ..interfaces import VoiceGenerator
from ..model import (
    LocalNarrationPreflight,
    LocalNarrationResult,
    LocalNarrationTask,
    MediaGenerationResult,
    ProductionMediaFailure,
    VoiceSynthesisTask,
)
from . import fake as _fake


GPT_SOVITS_PROVIDER = "local-gpt-sovits-v2"
GPT_SOVITS_REPOSITORY_COMMIT = "d523079fc05d9a8028d6085bffe4a2757c32abb6"
GPT_SOVITS_MODEL_IDENTIFIER = "gsv-v2final-pretrained"
GPT_SOVITS_INFERENCE_SCRIPT_BASENAME = "inference_cli.py"
GPT_SOVITS_GPT_MODEL_BASENAME = "s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"
GPT_SOVITS_SOVITS_MODEL_BASENAME = "s2G2333k.pth"
GPT_SOVITS_REFERENCE_PROVENANCE = "locally generated Qwen3-TTS Serena synthetic reference"
GPT_SOVITS_REFERENCE_TRANSCRIPT = "你好，我是小土豆。今天我们一起认识人工智能。"
_AUDIO_MEDIA_TYPE = "audio/mp4"
_MP4_FORMATS = frozenset({"mov,mp4,m4a,3gp,3g2,mj2"})
_BINDING_PREFIX = "ai-course-factory-gpt-sovits-v2:"
_MAX_AUDIO_BYTES = 64 * 1024 * 1024
_MAX_PROBE_BYTES = 1 * 1024 * 1024
_DURATION_TOLERANCE = 0.10
_SPOKEN_OVERFLOW_TOLERANCE = 0.02
_MAX_NARRATION_LENGTH = 4096
_MAX_DURATION = 3600
_G2PW_REQUIRED_FILES = (
    "config.py",
    "g2pW.onnx",
    "bopomofo_to_pinyin_wo_tune_dict.json",
    "char_bopomofo_dict.json",
    "POLYPHONIC_CHARS.txt",
    "MONOPHONIC_CHARS.txt",
)
_RUNTIME_DEPENDENCY_PROBE = (
    "import importlib\n"
    "for _name in (\n"
    "    'soundfile', 'torch', 'numpy', 'librosa', 'transformers', 'onnxruntime',\n"
    "    'torchaudio', 'gradio', 'peft', 'psutil', 'yaml', 'ffmpeg', 'pandas', 'scipy',\n"
    "):\n"
    "    importlib.import_module(_name)\n"
)


@dataclass(frozen=True, slots=True)
class GPTSoVITSConfiguration:
    """Operator-supplied external GPT-SoVITS runtime configuration."""

    external_python: str
    repository_root: str
    repository_commit: str
    inference_script: str
    tts_config: str
    gpt_model: str
    sovits_model: str
    reference_audio: str
    reference_transcript: str = GPT_SOVITS_REFERENCE_TRANSCRIPT
    model_identifier: str = GPT_SOVITS_MODEL_IDENTIFIER
    reference_language: str = "中文"
    target_language: str = "中文"
    ffmpeg_executable: str = "/opt/homebrew/bin/ffmpeg"
    ffprobe_executable: str = "/opt/homebrew/bin/ffprobe"
    timeout_seconds: int | float = 300


GPTSoVITSPreflight = LocalNarrationPreflight


Runner = Callable[..., subprocess.CompletedProcess[bytes]]


def _failure(code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure("validation", code, message)


def _generation_failure(code: str = "GPT_SOVITS_INFERENCE_FAILED") -> ProductionMediaFailure:
    return ProductionMediaFailure("execution", code, "local GPT-SoVITS narration failed safely")


def _storage_failure(code: str = "MEDIA_STORAGE_FAILED") -> ProductionMediaFailure:
    message = {
        "MEDIA_OUTPUT_CONFLICT": "media output reference conflicts with existing narration",
        "MEDIA_STORAGE_FAILED": "local narration output storage failed",
    }.get(code, "local narration output storage failed")
    return ProductionMediaFailure("execution", code, message)


def _number(value: object) -> float | None:
    if type(value) in (int, float):
        parsed = float(value)
    elif type(value) is str:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
    else:
        return None
    return parsed if math.isfinite(parsed) else None


def _duration_matches(actual: object, expected: int | float) -> bool:
    parsed = _number(actual)
    return parsed is not None and abs(parsed - float(expected)) <= _DURATION_TOLERANCE


def _valid_duration(value: object) -> bool:
    if type(value) is int:
        return 0 < value <= _MAX_DURATION
    return type(value) is float and math.isfinite(value) and 0 < value <= _MAX_DURATION


def _is_file(path: Path, *, executable: bool = False) -> bool:
    try:
        info = path.stat()
        return stat.S_ISREG(info.st_mode) and (not executable or os.access(path, os.X_OK))
    except (OSError, ValueError):
        return False


def _absolute_path(value: object) -> Path | None:
    if type(value) is not str or not value or not os.path.isabs(value):
        return None
    try:
        return Path(value).expanduser().resolve()
    except (OSError, TypeError, ValueError):
        return None


def _configured_path(value: object) -> Path | None:
    """Return the operator spelling without dereferencing a venv symlink."""

    if type(value) is not str or not value:
        return None
    try:
        path = Path(value).expanduser()
    except (OSError, TypeError, ValueError):
        return None
    return path if path.is_absolute() else None


def _workspace_payload(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"task_id": reference.task_id, "area": reference.area, "name": reference.name}


def _task_payload(task: VoiceSynthesisTask) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "attempt_id": task.attempt_id,
        "production_request_reference": {
            "artifact_type": task.production_request_reference.artifact_type,
            "identity": task.production_request_reference.identity,
            "version": task.production_request_reference.version,
        },
        "scene_id": task.scene_id,
        "language": task.language,
        "duration_seconds": task.duration_seconds,
        "narration": task.narration,
        "output_reference": _workspace_payload(task.output_reference),
    }


def _binding(task: VoiceSynthesisTask, config: GPTSoVITSConfiguration) -> str:
    payload = {
        "task": _task_payload(task),
        "engine": GPT_SOVITS_PROVIDER,
        "repository_commit": config.repository_commit,
        "model_identifier": config.model_identifier,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return _BINDING_PREFIX + hashlib.sha256(encoded).hexdigest()


def _safe_audio_bytes(path: Path) -> bytes | None:
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size < 1 or info.st_size > _MAX_AUDIO_BYTES:
            return None
        content = path.read_bytes()
        return content if type(content) is bytes and len(content) == info.st_size and len(content) <= _MAX_AUDIO_BYTES else None
    except (OSError, ValueError):
        return None


def _commit(workspace: WorkspaceAdapter, reference: WorkspaceFileReference, content: bytes) -> ProductionMediaFailure | None:
    try:
        result = workspace.commit(reference, content)
    except Exception:
        return _storage_failure()
    expected = WorkspaceFileRecord(reference, len(content))
    if type(result) is WorkspaceFileRecord and result == expected:
        return None
    if isinstance(result, WorkspaceFailure) and result.code == "WORKSPACE_FILE_CONFLICT":
        return _storage_failure("MEDIA_OUTPUT_CONFLICT")
    return _storage_failure()


class GPTSoVITSSyntheticVoiceGenerator(VoiceGenerator):
    """Generate normalized AAC narration with an explicitly configured runtime."""

    __slots__ = ("_workspace", "_config", "_runner", "_preflight_result")

    def __init__(
        self,
        workspace: WorkspaceAdapter,
        config: GPTSoVITSConfiguration,
        *,
        runner: Runner | None = None,
    ) -> None:
        self._workspace = workspace
        self._config = config
        self._runner = runner or subprocess.run
        self._preflight_result: GPTSoVITSPreflight | ProductionMediaFailure | None = None

    @property
    def configuration(self) -> GPTSoVITSConfiguration:
        return self._config

    @property
    def engine_metadata(self) -> Mapping[str, object]:
        """Additive package/UI facts; no local binary or path is returned."""

        return {
            "engine": GPT_SOVITS_PROVIDER,
            "engine_version": "v2",
            "repository_commit": self._config.repository_commit,
            "model_identifier": self._config.model_identifier,
            "runtime": "external Python 3.11 + GPT-SoVITS repository",
            "reference_provenance": GPT_SOVITS_REFERENCE_PROVENANCE,
            "reference_transcript": self._config.reference_transcript,
            "application_provider_api_call": False,
            "external_charge_micros": 0,
        }

    def preflight(self) -> GPTSoVITSPreflight | ProductionMediaFailure:
        """Validate every external input before inference or workspace writes."""

        if self._preflight_result is not None:
            return self._preflight_result

        config = self._config
        if type(config.repository_commit) is not str or config.repository_commit != GPT_SOVITS_REPOSITORY_COMMIT:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is invalid"))
        if config.model_identifier != GPT_SOVITS_MODEL_IDENTIFIER:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS model identifier is invalid"))
        if config.reference_transcript != GPT_SOVITS_REFERENCE_TRANSCRIPT or len(config.reference_transcript) > _MAX_NARRATION_LENGTH:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS reference transcript is invalid"))
        if config.reference_language not in {"中文", "英文", "日文"} or config.target_language not in {"中文", "英文", "日文", "中英混合", "日英混合", "多语种混合"}:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS language configuration is invalid"))
        if type(config.timeout_seconds) not in (int, float) or not math.isfinite(float(config.timeout_seconds)) or config.timeout_seconds < 1 or config.timeout_seconds > 1800:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is invalid"))

        external_python = _configured_path(config.external_python)
        external_python_real = _absolute_path(config.external_python)
        repository_root = _absolute_path(config.repository_root)
        inference_script = _absolute_path(config.inference_script)
        tts_config = _absolute_path(config.tts_config)
        gpt_model = _absolute_path(config.gpt_model)
        sovits_model = _absolute_path(config.sovits_model)
        reference_audio = _absolute_path(config.reference_audio)
        ffmpeg = _absolute_path(config.ffmpeg_executable)
        ffprobe = _absolute_path(config.ffprobe_executable)
        bert_base = repository_root / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large" if repository_root is not None else None
        cnhubert_base = repository_root / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base" if repository_root is not None else None
        g2pw_model = repository_root / "GPT_SoVITS" / "text" / "G2PWModel" if repository_root is not None else None
        if (
            external_python is None or external_python_real is None or not _is_file(external_python_real, executable=True)
            or repository_root is None or not repository_root.is_dir()
            or inference_script is None or not _is_file(inference_script)
            or tts_config is None or not _is_file(tts_config)
            or gpt_model is None or not _is_file(gpt_model)
            or sovits_model is None or not _is_file(sovits_model)
            or reference_audio is None or not _is_file(reference_audio)
            or ffmpeg is None or not _is_file(ffmpeg, executable=True)
            or ffprobe is None or not _is_file(ffprobe, executable=True)
            or bert_base is None or not bert_base.is_dir()
            or cnhubert_base is None or not cnhubert_base.is_dir()
            or g2pw_model is None or not g2pw_model.is_dir()
            or os.path.realpath(ffmpeg) == os.path.realpath(ffprobe)
        ):
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is incomplete"))
        try:
            if (
                not inference_script.is_relative_to(repository_root)
                or inference_script != repository_root / "GPT_SoVITS" / GPT_SOVITS_INFERENCE_SCRIPT_BASENAME
                or not tts_config.is_relative_to(repository_root)
                or not gpt_model.is_relative_to(repository_root)
                or not sovits_model.is_relative_to(repository_root)
                or gpt_model.name != GPT_SOVITS_GPT_MODEL_BASENAME
                or sovits_model.name != GPT_SOVITS_SOVITS_MODEL_BASENAME
                or gpt_model.parent != repository_root / "GPT_SoVITS" / "pretrained_models" / GPT_SOVITS_MODEL_IDENTIFIER
                or sovits_model.parent != repository_root / "GPT_SoVITS" / "pretrained_models" / GPT_SOVITS_MODEL_IDENTIFIER
            ):
                return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is incomplete"))
            config_text = tts_config.read_text(encoding="utf-8")
            if any(not _is_file(g2pw_model / name) for name in _G2PW_REQUIRED_FILES):
                return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is incomplete"))
        except (OSError, UnicodeError, ValueError):
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS runtime configuration is incomplete"))
        if "version: v2" not in config_text or "t2s_weights_path:" not in config_text or "vits_weights_path:" not in config_text:
            return self._remember_preflight(_failure("GPT_SOVITS_CONFIG_INVALID", "GPT-SoVITS v2 model configuration is incomplete"))

        with tempfile.TemporaryDirectory(prefix="acf-gpt-sovits-preflight-") as directory:
            preflight_root = Path(directory)
            preflight_cache = preflight_root / "numba-cache"
            preflight_cache.mkdir()
            runtime_env = self._runtime_environment(preflight_cache)
            version = self._run([str(external_python), "--version"], cwd=preflight_root, env=runtime_env)
            version_text = ((version.stdout or b"") + (version.stderr or b"")).decode("utf-8", "ignore") if version is not None else ""
            if version is None or version.returncode != 0 or not version_text.startswith("Python 3.11"):
                return self._remember_preflight(_failure("GPT_SOVITS_PYTHON_UNAVAILABLE", "an external Python 3.11 runtime is required"))
            dependencies = self._run([str(external_python), "-c", _RUNTIME_DEPENDENCY_PROBE], cwd=preflight_root, env=runtime_env)
            if dependencies is None or dependencies.returncode != 0:
                return self._remember_preflight(_failure("GPT_SOVITS_DEPENDENCIES_UNAVAILABLE", "the configured GPT-SoVITS Python runtime is missing required local dependencies"))

        git = self._run(["git", "-C", str(repository_root), "rev-parse", "HEAD"], cwd=repository_root)
        actual_commit = (git.stdout or b"").decode("ascii", "ignore").strip() if git is not None and git.returncode == 0 else ""
        if actual_commit != config.repository_commit:
            return self._remember_preflight(_failure("GPT_SOVITS_REPOSITORY_COMMIT_MISMATCH", "the configured GPT-SoVITS repository commit does not match"))

        probe = self._probe(reference_audio, ffprobe)
        if not self._valid_reference_probe(probe):
            return self._remember_preflight(_failure("GPT_SOVITS_REFERENCE_INVALID", "the configured GPT-SoVITS reference audio is not decodeable"))
        try:
            with tempfile.NamedTemporaryFile(prefix="acf-gpt-sovits-preflight-", delete=True) as handle:
                handle.write(b"preflight")
                handle.flush()
        except (OSError, ValueError):
            return self._remember_preflight(_failure("GPT_SOVITS_OUTPUT_UNAVAILABLE", "the local narration output boundary is unavailable"))
        return self._remember_preflight(GPTSoVITSPreflight(config.repository_commit, config.model_identifier, "reference audio", config.reference_transcript))

    def _remember_preflight(self, result: GPTSoVITSPreflight | ProductionMediaFailure) -> GPTSoVITSPreflight | ProductionMediaFailure:
        # A successful readiness snapshot is stable for the adapter lifetime,
        # but a failure can be transient (for example an operator repairs the
        # configured runtime path before retrying).  Keep legacy ``synthesize``
        # retry behaviour by never memoizing failures.
        if isinstance(result, LocalNarrationPreflight):
            self._preflight_result = result
        return result

    def render(self, task: LocalNarrationTask) -> LocalNarrationResult | ProductionMediaFailure:
        """Render through the additive local seam without touching paid-attempt facts."""

        if type(task) is not LocalNarrationTask:
            return ProductionMediaFailure("validation", "INVALID_LOCAL_NARRATION_TASK", "local narration task is invalid")
        voice_task = VoiceSynthesisTask(
            task.task_id,
            f"local-narration:{task.task_id}:{task.scene_id}",
            task.production_request_reference,
            task.scene_id,
            task.language,
            task.duration_seconds,
            task.narration,
            task.output_reference,
        )
        result = self.synthesize(voice_task)
        if isinstance(result, ProductionMediaFailure):
            return result
        if not isinstance(result, MediaGenerationResult):
            return ProductionMediaFailure("execution", "GPT_SOVITS_INFERENCE_FAILED", "local GPT-SoVITS narration failed safely")
        return LocalNarrationResult(
            task.task_id,
            task.scene_id,
            result.output_reference,
            result.media_type,
            result.duration_seconds,
            result.result_code,
        )

    def synthesize(self, task: VoiceSynthesisTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _fake._validate_voice(task)
        except _fake._InvalidTask as error:
            return ProductionMediaFailure("validation", error.code, "media generation task is invalid")
        except Exception:
            return ProductionMediaFailure("validation", "INVALID_VOICE_TASK", "media generation task is invalid")

        preflight = self.preflight()
        if isinstance(preflight, ProductionMediaFailure):
            return preflight
        binding = _binding(task, self._config)

        replay = self._replay(task, binding)
        if replay is not None:
            return replay

        with tempfile.TemporaryDirectory(prefix="acf-gpt-sovits-") as directory:
            root = Path(directory)
            ref_text = root / "reference.txt"
            target_text = root / "target.txt"
            raw_output = root / "output"
            normalized = root / "scene.m4a"
            raw_output.mkdir()
            numba_cache = root / "numba-cache"
            numba_cache.mkdir()
            runtime = root / "runtime"
            runtime.mkdir()
            try:
                # The official WebUI writes a relative weight.json at startup.
                # Keep that write inside this disposable runtime boundary while
                # exposing only the configured external GPT_SoVITS package.
                (runtime / "GPT_SoVITS").symlink_to(
                    Path(self._config.repository_root).expanduser().resolve() / "GPT_SoVITS",
                    target_is_directory=True,
                )
            except (OSError, ValueError):
                return _generation_failure("GPT_SOVITS_RUNTIME_UNAVAILABLE")
            try:
                ref_text.write_text(self._config.reference_transcript, encoding="utf-8")
                target_text.write_text(task.narration, encoding="utf-8")
            except (OSError, UnicodeError):
                return _generation_failure("GPT_SOVITS_INPUT_WRITE_FAILED")
            argv = [
                str(Path(self._config.external_python).expanduser()),
                str(Path(self._config.inference_script).expanduser().resolve()),
                "--gpt_model", str(Path(self._config.gpt_model).expanduser().resolve()),
                "--sovits_model", str(Path(self._config.sovits_model).expanduser().resolve()),
                "--ref_audio", str(Path(self._config.reference_audio).expanduser().resolve()),
                "--ref_text", str(ref_text),
                "--ref_language", self._config.reference_language,
                "--target_text", str(target_text),
                "--target_language", self._config.target_language,
                "--output_path", str(raw_output),
            ]
            result = self._run(
                argv,
                # The official CLI resolves its bundled G2PW model and writes
                # weight.json relative to cwd.  Use a disposable cwd with a
                # symlink to the explicit external GPT_SoVITS package so the
                # repository and application workspace remain untouched.
                cwd=runtime,
                env=self._runtime_environment(numba_cache),
            )
            if result is None or result.returncode != 0:
                return _generation_failure()
            generated = raw_output / "output.wav"
            if not self._normalize(generated, normalized, task.duration_seconds, binding):
                return _generation_failure("GPT_SOVITS_AUDIO_INVALID")
            content = _safe_audio_bytes(normalized)
            if content is None:
                return _generation_failure("GPT_SOVITS_AUDIO_INVALID")
        storage_failure = _commit(self._workspace, task.output_reference, content)
        if storage_failure is not None:
            return storage_failure
        return MediaGenerationResult(task.attempt_id, task.scene_id, "voice", GPT_SOVITS_PROVIDER, task.output_reference, _AUDIO_MEDIA_TYPE, task.duration_seconds, "SUCCESS")

    def _runtime_environment(self, numba_cache: Path | None = None) -> dict[str, str]:
        """Bind the official CLI to explicit local paths without repo writes/network."""

        repository = Path(self._config.repository_root).expanduser().resolve()
        gpt_sovits = repository / "GPT_SoVITS"
        eres2net = gpt_sovits / "eres2net"
        pythonpath = os.pathsep.join(str(item) for item in (repository, gpt_sovits, eres2net) if item.is_dir())
        environment = {
            key: value
            for key, value in os.environ.items()
            if key in {"PATH", "LANG", "TERM"} or key.startswith("LC_")
        }
        environment.update({
            "PYTHONPATH": pythonpath,
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONNOUSERSITE": "1",
            "version": "v2",
            "is_half": "False",
            "gpt_path": str(Path(self._config.gpt_model).expanduser().resolve()),
            "sovits_path": str(Path(self._config.sovits_model).expanduser().resolve()),
            "bert_path": str(repository / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large"),
            "cnhubert_base_path": str(repository / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base"),
        })
        if numba_cache is not None:
            environment["NUMBA_CACHE_DIR"] = str(numba_cache)
            boundary = numba_cache.parent
            home = boundary / "home"
            home.mkdir(parents=True, exist_ok=True)
            environment.update({"HOME": str(home), "TMPDIR": str(boundary), "TEMP": str(boundary), "TMP": str(boundary)})
        return environment

    def _run(
        self,
        argv: list[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes] | None:
        if type(argv) is not list or not argv or not all(type(item) is str and item for item in argv):
            return None
        try:
            result = self._runner(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                cwd=str(cwd) if cwd is not None else None,
                timeout=self._config.timeout_seconds,
                check=False,
                **({"env": dict(env)} if env is not None else {}),
            )
            return result if isinstance(result, subprocess.CompletedProcess) else None
        except (OSError, subprocess.SubprocessError, ValueError, TypeError):
            return None

    def _probe(self, path: Path, ffprobe: Path) -> Mapping[str, Any] | None:
        result = self._run([
            str(ffprobe), "-hide_banner", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,sample_rate,channels,duration:format=format_name,duration:format_tags=comment",
            "-of", "json", str(path),
        ], cwd=path.parent)
        if result is None or result.returncode != 0 or type(result.stdout) is not bytes or len(result.stdout) > _MAX_PROBE_BYTES:
            return None
        try:
            parsed = json.loads(result.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            return None
        return parsed if isinstance(parsed, Mapping) else None

    @staticmethod
    def _valid_reference_probe(probe: Mapping[str, Any] | None) -> bool:
        if not isinstance(probe, Mapping) or not isinstance(probe.get("streams"), list) or len(probe["streams"]) != 1 or not isinstance(probe["streams"][0], Mapping):
            return False
        stream = probe["streams"][0]
        duration = _number(stream.get("duration"))
        return stream.get("codec_type") == "audio" and duration is not None and duration > 0 and isinstance(probe.get("format"), Mapping)

    def _replay(self, task: VoiceSynthesisTask, binding: str) -> MediaGenerationResult | ProductionMediaFailure | None:
        try:
            content = self._workspace.read(task.output_reference)
        except Exception:
            return None
        if isinstance(content, WorkspaceFailure):
            return None if content.code == "WORKSPACE_FILE_NOT_FOUND" else _storage_failure()
        if type(content) is not bytes:
            return _storage_failure()
        with tempfile.TemporaryDirectory(prefix="acf-gpt-sovits-replay-") as directory:
            path = Path(directory) / "scene.m4a"
            try:
                path.write_bytes(content)
            except OSError:
                return _storage_failure()
            probe = self._probe(path, Path(self._config.ffprobe_executable).expanduser().resolve())
        tags = probe.get("format", {}).get("tags", {}) if isinstance(probe, Mapping) and isinstance(probe.get("format"), Mapping) else {}
        if isinstance(tags, Mapping) and tags.get("comment") == binding and self._valid_normalized_probe(probe, task.duration_seconds):
            return MediaGenerationResult(task.attempt_id, task.scene_id, "voice", GPT_SOVITS_PROVIDER, task.output_reference, _AUDIO_MEDIA_TYPE, task.duration_seconds, "SUCCESS")
        return _storage_failure("MEDIA_OUTPUT_CONFLICT")

    def _normalize(self, source: Path, output: Path, duration: int | float, binding: str) -> bool:
        if not _valid_duration(duration):
            return False
        content = _safe_audio_bytes(source)
        if content is None:
            return False
        ffprobe = Path(self._config.ffprobe_executable).expanduser().resolve()
        probe = self._probe(source, ffprobe)
        if not isinstance(probe, Mapping) or not isinstance(probe.get("streams"), list) or len(probe["streams"]) != 1 or not isinstance(probe["streams"][0], Mapping):
            return False
        actual = _number(probe["streams"][0].get("duration"))
        if actual is None or actual <= 0 or actual > float(duration) + _SPOKEN_OVERFLOW_TOLERANCE:
            return False
        pad = max(0.0, float(duration) - actual)
        pad_text = f"{pad:.6f}"
        argv = [
            str(Path(self._config.ffmpeg_executable).expanduser().resolve()), "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(source), "-vn", "-af", f"apad=pad_dur={pad_text}", "-t", f"{float(duration):.6f}",
            "-c:a", "aac", "-b:a", "64k", "-ar", "48000", "-ac", "1", "-map_metadata", "-1",
            "-metadata", "creation_time=1970-01-01T00:00:00Z", "-metadata", f"comment={binding}", "-movflags", "+faststart", str(output),
        ]
        result = self._run(argv, cwd=source.parent)
        if result is None or result.returncode != 0:
            return False
        normalized = _safe_audio_bytes(output)
        if normalized is None:
            return False
        return self._valid_normalized_probe(self._probe(output, ffprobe), duration)

    @staticmethod
    def _valid_normalized_probe(probe: Mapping[str, Any] | None, duration: int | float) -> bool:
        if not isinstance(probe, Mapping) or not isinstance(probe.get("streams"), list) or len(probe["streams"]) != 1 or not isinstance(probe["streams"][0], Mapping):
            return False
        stream = probe["streams"][0]
        format_value = probe.get("format")
        return (
            stream.get("codec_type") == "audio"
            and stream.get("codec_name") == "aac"
            and stream.get("sample_rate") in {"48000", 48000}
            and stream.get("channels") == 1
            and _duration_matches(stream.get("duration"), duration)
            and isinstance(format_value, Mapping)
            and format_value.get("format_name") in _MP4_FORMATS
        )


GPTSoVITSVoiceGenerator = GPTSoVITSSyntheticVoiceGenerator


__all__ = [
    "GPT_SOVITS_PROVIDER",
    "GPT_SOVITS_MODEL_IDENTIFIER",
    "GPT_SOVITS_GPT_MODEL_BASENAME",
    "GPT_SOVITS_SOVITS_MODEL_BASENAME",
    "GPT_SOVITS_REFERENCE_PROVENANCE",
    "GPT_SOVITS_REFERENCE_TRANSCRIPT",
    "GPT_SOVITS_REPOSITORY_COMMIT",
    "GPTSoVITSConfiguration",
    "GPTSoVITSPreflight",
    "GPTSoVITSVoiceGenerator",
    "GPTSoVITSSyntheticVoiceGenerator",
]
