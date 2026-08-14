"""Server-rendered Review behavior for the explicit Storyboard gate."""

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.web import create_app
from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL


def _client(directory: str) -> TestClient:
    client = TestClient(
        create_app(Path(directory), source_connector=FixtureSourceConnector()),
        base_url="http://127.0.0.1",
    )
    started = client.post(
        "/start/source",
        data={"repository_url": SUPPORTED_REPOSITORY_URL},
        headers={"Origin": "http://127.0.0.1"},
        follow_redirects=False,
    )
    if started.status_code != 303:
        raise AssertionError(started.text)
    return client


def _post(client: TestClient, path: str, data: dict[str, str]):
    return client.post(path, data=data, headers={"Origin": "http://127.0.0.1"}, follow_redirects=False)


def _storyboard_approval_snapshot(directory: str) -> tuple[object, ...]:
    """Capture the durable H1 refs/decision counts without a new test seam."""
    with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
        state_json = connection.execute(
            "SELECT state_json FROM application_state WHERE singleton = 1"
        ).fetchone()[0]
        state = json.loads(state_json)
        refs = tuple(
            (
                name,
                state["refs"][name]["artifact_type"],
                state["refs"][name]["identity"],
                state["refs"][name]["version"],
            )
            for name in ("storyboard", "timeline", "production_request", "scene_generation_contract")
        )
        decision_rows = tuple(
            connection.execute(
                "SELECT decision_id, action, decision_context FROM storyboard_decisions ORDER BY decision_id"
            ).fetchall()
        )
        version_counts = tuple(
            connection.execute(
                "SELECT artifact_type, COUNT(*) FROM artifact_versions "
                "WHERE artifact_type IN ('timeline', 'production_request', 'scene_generation_contract') "
                "GROUP BY artifact_type ORDER BY artifact_type"
            ).fetchall()
        )
    return refs, state["decision_ids"].get("storyboard"), decision_rows, version_counts


class SceneGenerationContractWebTests(unittest.TestCase):
    def test_review_posts_storyboard_approval_and_renders_contract_entries(self):
        with TemporaryDirectory() as directory:
            client = _client(directory)
            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})

            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            self.assertIn("通过分镜", review.text)
            self.assertIn('name="decision_context"', review.text)
            self.assertIn("六段场景一览", review.text)

            approved = _post(client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(approved.status_code, 303)
            self.assertEqual(approved.headers["location"], "/review")
            ready = client.get("/review")
            self.assertEqual(ready.status_code, 200)
            self.assertIn("handoff_readiness", ready.text)
            self.assertIn("场景生成合同", ready.text)
            self.assertIn("scene-1.mp4", ready.text)
            self.assertIn("scene-6.mp4", ready.text)
            self.assertEqual(ready.text.count('data-view-kind="'), 1)

    def test_repeated_storyboard_approval_post_replays_after_restart_without_new_versions(self):
        with TemporaryDirectory() as directory:
            first_app = create_app(Path(directory), source_connector=FixtureSourceConnector())
            first_client = TestClient(first_app, base_url="http://127.0.0.1")
            started = _post(
                first_client,
                "/start/source",
                {"repository_url": SUPPORTED_REPOSITORY_URL},
            )
            self.assertEqual(started.status_code, 303)
            self.assertEqual(_post(first_client, "/start/script", {"action": "approve_script"}).status_code, 303)
            self.assertEqual(_post(first_client, "/review/action", {"action": "advance_planning"}).status_code, 303)

            first_approval = _post(first_client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(first_approval.status_code, 303)
            self.assertEqual(first_approval.headers["location"], "/review")
            after_first = _storyboard_approval_snapshot(directory)

            reject_after_approval = _post(
                first_client,
                "/review/action",
                {"action": "reject_storyboard", "decision_context": "must remain gated"},
            )
            self.assertEqual(reject_after_approval.status_code, 400)
            self.assertEqual(_storyboard_approval_snapshot(directory), after_first)

            repeated = _post(first_client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(repeated.status_code, 303)
            self.assertEqual(repeated.headers["location"], "/review")
            self.assertEqual(_storyboard_approval_snapshot(directory), after_first)

            first_app.state.course_factory.close()
            resumed_app = create_app(Path(directory), source_connector=FixtureSourceConnector())
            resumed_client = TestClient(resumed_app, base_url="http://127.0.0.1")
            replayed = _post(resumed_client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(replayed.status_code, 303)
            self.assertEqual(replayed.headers["location"], "/review")
            self.assertEqual(_storyboard_approval_snapshot(directory), after_first)
            self.assertEqual(len(after_first[2]), 1)
            self.assertEqual(dict(after_first[3]), {"production_request": 1, "scene_generation_contract": 1, "timeline": 1})

    def test_reject_context_is_read_only_and_approve_starts_empty_independent_decision(self):
        with TemporaryDirectory() as directory:
            client = _client(directory)
            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})

            context = "Keep the same storyboard; revisit the opening rhythm."
            rejected = _post(
                client,
                "/review/action",
                {"action": "reject_storyboard", "decision_context": context},
            )
            self.assertEqual(rejected.status_code, 303)
            review = client.get("/review")
            self.assertIn(context, review.text)
            self.assertIn("分镜仍可使用", review.text)
            self.assertIn('id="storyboard-decision-context" name="decision_context"', review.text)

            approved = _post(client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(approved.status_code, 303)
            with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
                decisions = {
                    row[0]: (row[1], row[2])
                    for row in connection.execute(
                        "SELECT decision_id, action, decision_context "
                        "FROM storyboard_decisions "
                        "WHERE decision_id IN (?, ?)",
                        ("decision:storyboard:v1:reject", "decision:storyboard:v1:approve"),
                    )
                }
            self.assertEqual(decisions["decision:storyboard:v1:reject"], ("reject", context))
            self.assertEqual(decisions["decision:storyboard:v1:approve"], ("approve", ""))
            self.assertNotEqual("decision:storyboard:v1:reject", "decision:storyboard:v1:approve")


if __name__ == "__main__":
    unittest.main()
