"""Facade behavior for the explicit local GPT-SoVITS path."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.production import GPTSoVITSConfiguration
from tests.legacy_v11_fixture import seed_legacy_budget_review
from tests.source_fixture import FixtureSourceConnector, ensure_source


def _invalid_config() -> GPTSoVITSConfiguration:
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


class GPTSoVITSFacadeTests(unittest.TestCase):
    def test_missing_explicit_runtime_fails_before_any_voice_attempt_or_fixture_fallback(self):
        with TemporaryDirectory() as directory:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), tts_configuration=_invalid_config())
            ensure_source(app)
            seed_legacy_budget_review(app)
            approved = app.submit_budget_decision("approve")
            self.assertEqual(approved.status, "success")

            result = app.produce_offline()

            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "GPT_SOVITS_CONFIG_INVALID")
            self.assertEqual(result.view.stage, "production")
            self.assertEqual(result.view.provider_attempt_count, 0)
            self.assertEqual(result.view.tts_engine, "local-gpt-sovits-v2")
            self.assertNotIn("Fixture", result.error_message or "")


if __name__ == "__main__":
    unittest.main()
