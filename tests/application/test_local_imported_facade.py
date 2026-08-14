from __future__ import annotations

from pathlib import Path
import io
import json
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest
import zipfile

from ai_course_factory.application import CourseFactoryApplication
from tests.source_fixture import REAL_SHAPED_COMMIT, FixtureSourceConnector, ensure_source


def _app(path: str | Path, **kwargs: object) -> CourseFactoryApplication:
    app = CourseFactoryApplication(path, source_connector=FixtureSourceConnector(), **kwargs)
    ensure_source(app)
    return app


def _tool(name: str, fallback: str) -> str:
    return shutil.which(name) or fallback


def _write_png(path: Path, colour: str) -> None:
    subprocess.run(
        [
            _tool("ffmpeg", "/opt/homebrew/bin/ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s=32x32",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class LocalImportedFacadeTests(unittest.TestCase):
    def _advance_to_production(self, app: CourseFactoryApplication) -> None:
        self.assertEqual(app.create_or_open().status, "success")
        self.assertEqual(app.submit_script_decision("approve").status, "success")
        self.assertEqual(app.advance_planning().status, "success")
        self.assertEqual(app.submit_budget_decision("approve").status, "success")

    def test_imported_mode_preflights_atomically_and_exposes_six_prompt_cards(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            app = _app(root / "data", visual_import_dir=imports)
            self._advance_to_production(app)

            cards = app.inspect().view.prompt_cards
            self.assertEqual(len(cards), 6)
            self.assertEqual(
                tuple(card.target_filename for card in cards),
                tuple(f"scene-{index}.png" for index in range(1, 7)),
            )
            self.assertEqual(tuple(card.scene_id for card in cards), tuple(f"scene-{index}" for index in range(1, 7)))
            self.assertEqual(cards[0].character_action, "挥手。")
            self.assertEqual(cards[1].character_action, "转身。")
            self.assertNotEqual(cards[0].scene_intent, cards[1].scene_intent)
            self.assertEqual(len({card.style_character_continuity for card in cards}), 1)
            for card in cards:
                self.assertIn("9:16", card.prompt)
                self.assertIn("No text, no watermark.", card.prompt)
            failed = app.produce_offline()

            self.assertEqual(failed.status, "failure")
            self.assertEqual(failed.error_code, "LOCAL_IMPORT_PREFLIGHT_FAILED")
            self.assertEqual(failed.view.provider_attempt_count, 0)
            self.assertFalse(any((imports / f"scene-{index}.png").exists() for index in range(1, 7)))
            self.assertNotIsInstance(
                app.workspace.read(failed.view.scenes[0].selected_clip_reference)
                if failed.view.scenes[0].selected_clip_reference
                else None,
                bytes,
            )

    def test_explicit_invalid_import_directory_fails_closed_without_fixture_fallback(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(Path(directory) / "data", visual_import_dir=Path("\0"))
            self._advance_to_production(app)
            self.assertEqual(app.inspect().view.visual_mode, "imported")
            failed = app.produce_offline()
            self.assertEqual(failed.status, "failure")
            self.assertEqual(failed.error_code, "LOCAL_IMPORT_DIRECTORY_REQUIRED")
            self.assertEqual(failed.view.provider_attempt_count, 0)
            app.close()

    def test_imported_production_replacement_is_visual_only_and_replays_after_restart(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            colours = ("red", "blue", "green", "yellow", "purple", "orange")
            for index, colour in enumerate(colours, start=1):
                _write_png(imports / f"scene-{index}.png", colour)
            app = _app(root / "data", visual_import_dir=imports)
            self._advance_to_production(app)

            produced = app.produce_offline()

            self.assertEqual(produced.status, "success")
            self.assertEqual(produced.view.provider_attempt_count, 12)
            before_clips = tuple(scene.selected_clip_reference for scene in produced.view.scenes)
            before_audio = tuple(scene.selected_audio_reference for scene in produced.view.scenes)
            before_video = produced.view.video_reference
            before_video_payload = self._video_payload(app, before_video)
            before_master_audio = before_video_payload["master_audio_reference"]
            before_stage = produced.view.stage
            before_pending_action = produced.view.pending_action
            before_failure_category = produced.view.failure_category
            before_failure_message = produced.view.failure_message
            before_replacement_done = produced.view.replacement_done

            missing = app.replace_scene("scene-2")
            self.assertEqual(missing.status, "failure")
            self.assertEqual(missing.error_code, "LOCAL_IMPORT_REPLACEMENT_PREFLIGHT_FAILED")
            self.assertFalse(missing.view.replacement_done)
            self.assertEqual(missing.view.video_reference, before_video)
            self.assertEqual(tuple(scene.selected_clip_reference for scene in missing.view.scenes), before_clips)
            self.assertEqual(tuple(scene.selected_audio_reference for scene in missing.view.scenes), before_audio)

            app.close()
            resumed_missing = _app(root / "data", visual_import_dir=imports)
            replay_before_replacement = resumed_missing.create_or_open()
            self.assertEqual(replay_before_replacement.view.stage, before_stage)
            self.assertEqual(replay_before_replacement.view.pending_action, before_pending_action)
            self.assertEqual(replay_before_replacement.view.video_reference, before_video)
            self.assertEqual(replay_before_replacement.view.failure_category, before_failure_category)
            self.assertEqual(replay_before_replacement.view.failure_message, before_failure_message)
            self.assertEqual(replay_before_replacement.view.replacement_done, before_replacement_done)

            (imports / "scene-2-replacement.png").write_bytes(b"not-an-image")
            invalid = resumed_missing.replace_scene("scene-2")
            self.assertEqual(invalid.status, "failure")
            self.assertEqual(invalid.error_code, "LOCAL_IMPORT_REPLACEMENT_PREFLIGHT_FAILED")
            resumed_missing.close()
            reopened_invalid = _app(root / "data", visual_import_dir=imports)
            replay_after_invalid = reopened_invalid.create_or_open()
            self.assertEqual(replay_after_invalid.view.stage, before_stage)
            self.assertEqual(replay_after_invalid.view.pending_action, before_pending_action)
            self.assertEqual(replay_after_invalid.view.failure_category, before_failure_category)
            self.assertEqual(replay_after_invalid.view.failure_message, before_failure_message)

            _write_png(imports / "scene-2-replacement.png", "pink")
            replaced = reopened_invalid.replace_scene("scene-2")
            self.assertEqual(replaced.status, "success")
            self.assertTrue(replaced.view.replacement_done)
            self.assertNotEqual(replaced.view.scenes[1].selected_clip_reference, before_clips[1])
            self.assertEqual(replaced.view.scenes[1].selected_audio_reference, before_audio[1])
            for index in (0, 2, 3, 4, 5):
                self.assertEqual(replaced.view.scenes[index].selected_clip_reference, before_clips[index])
                self.assertEqual(replaced.view.scenes[index].selected_audio_reference, before_audio[index])
            self.assertEqual(replaced.view.provider_attempt_count, 12)
            replaced_video_payload = self._video_payload(reopened_invalid, replaced.view.video_reference)
            self.assertEqual(replaced_video_payload["master_audio_reference"], before_master_audio)

            replacement_video = replaced.view.video_reference
            reopened_invalid.close()
            resumed = _app(root / "data", visual_import_dir=imports)
            replay = resumed.create_or_open()
            self.assertEqual(replay.status, "success")
            self.assertTrue(replay.view.replacement_done)
            self.assertEqual(replay.view.video_reference, replacement_video)

            self.assertEqual(resumed.submit_final_decision("approve").status, "success")
            exported = resumed.export_package()
            self.assertEqual(exported.status, "success")
            package_bytes = resumed.workspace.read(exported.view.package_output)
            with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
                attribution = json.loads(archive.read("source-attribution.json"))
            self.assertEqual(attribution["repository_url"], "https://github.com/microsoft/AI-For-Beginners")
            self.assertEqual(attribution["commit_sha"], REAL_SHAPED_COMMIT)
            self.assertTrue(attribution["units"])
            visuals = attribution["visual_assets"]
            self.assertEqual(visuals["creator_supplied_via"], "creator-supplied via ChatGPT Desktop ImageGen")
            self.assertTrue(visuals["generated_outside_application"])
            self.assertEqual(visuals["model_version"], "not verified by application")
            self.assertFalse(visuals["application_provider_api_call"])
            self.assertEqual(visuals["external_charge_micros"], 0)
            self.assertEqual(visuals["selected_assets"][1]["target_filename"], "scene-2-replacement.png")

    @staticmethod
    def _video_payload(app: CourseFactoryApplication, reference):
        return app.artifacts.get(reference).payload


if __name__ == "__main__":
    unittest.main()
