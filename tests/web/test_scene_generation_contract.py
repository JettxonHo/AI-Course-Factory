"""Server-rendered Review behavior for the explicit Storyboard gate."""

from pathlib import Path
from tempfile import TemporaryDirectory
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


class SceneGenerationContractWebTests(unittest.TestCase):
    def test_review_posts_storyboard_approval_and_renders_contract_entries(self):
        with TemporaryDirectory() as directory:
            client = _client(directory)
            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})

            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            self.assertIn("Approve storyboard", review.text)
            self.assertIn('name="decision_context"', review.text)
            self.assertIn("Storyboard at a glance", review.text)

            approved = _post(client, "/review/action", {"action": "approve_storyboard"})
            self.assertEqual(approved.status_code, 303)
            self.assertEqual(approved.headers["location"], "/review")
            ready = client.get("/review")
            self.assertEqual(ready.status_code, 200)
            self.assertIn("handoff_readiness", ready.text)
            self.assertIn("Scene Generation Contract", ready.text)
            self.assertIn("scene-1.mp4", ready.text)
            self.assertIn("scene-6.mp4", ready.text)
            self.assertEqual(ready.text.count('data-view-kind="'), 1)

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
            self.assertIn(f"Last decision context: {context}", review.text)
            self.assertIn(
                '<textarea id="storyboard-decision-context" name="decision_context" rows="3" maxlength="128" placeholder="Why this storyboard is ready, or what should be reconsidered."></textarea>',
                review.text,
            )

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
