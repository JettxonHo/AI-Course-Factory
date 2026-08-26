from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.application import CourseFactoryApplication

from tests.source_fixture import (
    REAL_SHAPED_BLOB,
    REAL_SHAPED_COMMIT,
    SUPPORTED_REPOSITORY_URL,
    FixtureSourceConnector,
)


COMPUTER_VISION_PATH = "lessons/4-ComputerVision/06-IntroCV/README.md"
PACKAGE_IDS = (
    "computer-vision-episode-01-pixels",
    "computer-vision-episode-02-preprocessing",
    "computer-vision-episode-03-motion",
)
EPISODE_CONTRACTS = (
    {
        "package_id": PACKAGE_IDS[0],
        "source_unit_index": 2,  # ### Loading Images
        "claim": "Images in Python can be conveniently represented by NumPy arrays.",
        "narration": "像素图像可以表示为 NumPy 数组。",
    },
    {
        "package_id": PACKAGE_IDS[1],
        "source_unit_index": 3,  # ### Image Processing
        "claim": "Resizing and brightness and contrast adjustments are image pre-processing steps.",
        "narration": "预处理可以调整图像尺寸、亮度和对比度。",
    },
    {
        "package_id": PACKAGE_IDS[2],
        "source_unit_index": 4,  # ## Examples of using Computer Vision
        "claim": "Frame difference and optical flow help detect movement in video.",
        "narration": "帧差和光流可以帮助检测视频中的运动。",
    },
)


def _package(package_id: str, locator: str, claim: str, narration: str) -> dict[str, object]:
    return {
        "schema": "ai-course-factory.creator-script-package",
        "version": 1,
        "script_package_id": package_id,
        "source": {
            "repository_url": SUPPORTED_REPOSITORY_URL,
            "repository_identity": "microsoft/AI-For-Beginners",
            "commit_sha": REAL_SHAPED_COMMIT,
            "files": [{"path": COMPUTER_VISION_PATH, "blob_sha": REAL_SHAPED_BLOB}],
        },
        "claims": [{"claim_id": f"{package_id}-claim", "statement": claim, "evidence_locators": [locator]}],
        "narration_units": [{"unit_id": f"{package_id}-unit", "text": narration, "claim_ids": [f"{package_id}-claim"]}],
        "creator_provenance": {
            "creator_declared_name": "Creator",
            "creator_role": "teacher",
            "tool_name": "ChatGPT",
        },
        "revision_note": None,
    }


class ComputerVisionSeriesReadinessTests(unittest.TestCase):
    def test_three_fresh_roots_bind_distinct_packages_and_replay_without_production_state(self) -> None:
        """Each fixed episode package binds one acquired Source in its own root."""
        self.assertEqual(len(set(PACKAGE_IDS)), 3)
        bound_locators: list[str] = []
        for contract in EPISODE_CONTRACTS:
            package_id = contract["package_id"]
            with self.subTest(package_id=package_id), TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
                connector = FixtureSourceConnector()
                app = CourseFactoryApplication(
                    Path(directory),
                    source_connector=connector,
                    script_package_directory=package_dir,
                )
                started = app.start_source(SUPPORTED_REPOSITORY_URL)
                self.assertEqual(started.status, "success")
                self.assertEqual(connector.calls, [(SUPPORTED_REPOSITORY_URL, (COMPUTER_VISION_PATH,))])
                self.assertGreaterEqual(len(started.view.source_evidence), 5)
                locator = started.view.source_evidence[contract["source_unit_index"]]
                bound_locators.append(locator)
                Path(package_dir, "creator-script.json").write_text(
                    json.dumps(_package(package_id, locator, contract["claim"], contract["narration"])), encoding="utf-8"
                )

                imported = app.import_creator_script_package()

                self.assertEqual(imported.status, "success")
                self.assertEqual(imported.view.creator_script_package_id, package_id)
                self.assertEqual(imported.view.pending_action, "approve_script")
                self.assertEqual(imported.view.creator_script_decision_id, None)
                self.assertIn(locator, imported.view.source_evidence)
                self.assertEqual(len(imported.view.creator_script_claims), 1)
                self.assertEqual(imported.view.creator_script_claims[0].claim_id, f"{package_id}-claim")
                self.assertEqual(imported.view.creator_script_claims[0].statement, contract["claim"])
                self.assertEqual(imported.view.creator_script_claims[0].evidence_locators, (locator,))
                self.assertEqual(len(imported.view.creator_script_narration_units), 1)
                self.assertEqual(imported.view.creator_script_narration_units[0].unit_id, f"{package_id}-unit")
                self.assertEqual(imported.view.creator_script_narration_units[0].text, contract["narration"])
                self.assertEqual(imported.view.creator_script_narration_units[0].claim_ids, (f"{package_id}-claim",))
                self.assertEqual(app.artifacts._connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'").fetchone()[0], 1)
                self.assertEqual(app.creator_script_decisions.count(), 0)
                self.assertEqual(app.budget_decisions._connection.execute("SELECT COUNT(*) FROM budget_decisions").fetchone()[0], 0)
                self.assertEqual(app.budget_decisions._connection.execute("SELECT COUNT(*) FROM budget_authorizations").fetchone()[0], 0)
                self.assertEqual(app.attempts._connection.execute("SELECT COUNT(*) FROM provider_attempts").fetchone()[0], 0)
                raw_before = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]
                app.close()

                resumed_connector = FixtureSourceConnector()
                resumed = CourseFactoryApplication(
                    Path(directory),
                    source_connector=resumed_connector,
                    script_package_directory=package_dir,
                )
                replay = resumed.import_creator_script_package()

                self.assertEqual(replay.status, "success")
                self.assertEqual(replay.view.creator_script_package_id, package_id)
                self.assertEqual(replay.view.script_reference.version, 1)
                self.assertEqual(replay.view.source_commit, started.view.source_commit)
                self.assertEqual(replay.view.source_evidence, started.view.source_evidence)
                self.assertEqual(replay.view.creator_script_claims[0].evidence_locators, (locator,))
                self.assertEqual(replay.view.creator_script_narration_units[0].text, contract["narration"])
                self.assertEqual(resumed_connector.calls, [])
                self.assertEqual(resumed._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0], raw_before)
                self.assertEqual(resumed.artifacts._connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'").fetchone()[0], 1)
                self.assertEqual(resumed.creator_script_decisions.count(), 0)

        self.assertEqual(len(set(bound_locators)), 3)


if __name__ == "__main__":
    unittest.main()
