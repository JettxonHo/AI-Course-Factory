"""Minimal three-view presentation of local GPT-SoVITS facts."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave

from fastapi.testclient import TestClient

from ai_course_factory.production import (
    GPT_SOVITS_GPT_MODEL_BASENAME,
    GPT_SOVITS_MODEL_IDENTIFIER,
    GPT_SOVITS_SOVITS_MODEL_BASENAME,
    GPTSoVITSConfiguration,
)
from ai_course_factory.web import create_app
from tests.source_fixture import SUPPORTED_REPOSITORY_URL, FixtureSourceConnector


def _config() -> GPTSoVITSConfiguration:
    return GPTSoVITSConfiguration(
        external_python="/missing/python311",
        repository_root="/missing/gpt-sovits-repo",
        repository_commit="d523079fc05d9a8028d6085bffe4a2757c32abb6",
        inference_script="/missing/inference_cli.py",
        tts_config="/missing/tts_infer.yaml",
        gpt_model="/missing/gpt.ckpt",
        sovits_model="/missing/sovits.pth",
        reference_audio="/missing/reference.wav",
    )


class GPTSoVITSWebTests(unittest.TestCase):
    def test_start_view_shows_engine_reference_and_zero_charge_without_raw_config(self):
        with TemporaryDirectory() as directory:
            client = TestClient(create_app(Path(directory), source_connector=FixtureSourceConnector(), tts_configuration=_config()), base_url="http://127.0.0.1")
            started = client.post("/start/source", data={"repository_url": SUPPORTED_REPOSITORY_URL}, headers={"Origin": "http://127.0.0.1"}, follow_redirects=False)
            self.assertEqual(started.status_code, 303)
            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("local-gpt-sovits-v2", response.text)
            self.assertIn("locally generated Qwen3-TTS Serena synthetic reference", response.text)
            self.assertIn("外部费用 0 micros", response.text)
            self.assertNotIn("/missing/", response.text)

    def test_configured_runtime_facts_are_visible_on_each_of_the_three_views(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            model_dir = repo / "GPT_SoVITS" / "pretrained_models" / GPT_SOVITS_MODEL_IDENTIFIER
            model_dir.mkdir(parents=True)
            (repo / "GPT_SoVITS" / "configs").mkdir(parents=True)
            (repo / "GPT_SoVITS" / "inference_cli.py").write_text("# configured fixture CLI\n", encoding="utf-8")
            (repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml").write_text(
                "version: v2\nt2s_weights_path: s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt\n"
                "vits_weights_path: s2G2333k.pth\n",
                encoding="utf-8",
            )
            gpt_model = model_dir / GPT_SOVITS_GPT_MODEL_BASENAME
            sovits_model = model_dir / GPT_SOVITS_SOVITS_MODEL_BASENAME
            gpt_model.write_bytes(b"fixture")
            sovits_model.write_bytes(b"fixture")
            reference = root / "reference.wav"
            with wave.open(str(reference), "wb") as handle:
                handle.setnchannels(1)
                handle.setsampwidth(2)
                handle.setframerate(24000)
                handle.writeframes(b"\0\0" * 2400)
            executable = root / "python311"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            config = GPTSoVITSConfiguration(
                external_python=str(executable),
                repository_root=str(repo),
                repository_commit="d523079fc05d9a8028d6085bffe4a2757c32abb6",
                inference_script=str(repo / "GPT_SoVITS" / "inference_cli.py"),
                tts_config=str(repo / "GPT_SoVITS" / "configs" / "tts_infer.yaml"),
                gpt_model=str(gpt_model),
                sovits_model=str(sovits_model),
                reference_audio=str(reference),
            )
            client = TestClient(create_app(root / "data", source_connector=FixtureSourceConnector(), tts_configuration=config), base_url="http://127.0.0.1")
            started = client.post("/start/source", data={"repository_url": SUPPORTED_REPOSITORY_URL}, headers={"Origin": "http://127.0.0.1"}, follow_redirects=False)
            self.assertEqual(started.status_code, 303)
            for route in ("/", "/review", "/final"):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertIn("local-gpt-sovits-v2", response.text)
                self.assertIn("locally generated Qwen3-TTS Serena synthetic reference", response.text)
                self.assertIn("外部费用", response.text)
                self.assertIn("0 micros", response.text)
            self.assertEqual(client.get("/").text.count("data-view-kind="), 1)


if __name__ == "__main__":
    unittest.main()
