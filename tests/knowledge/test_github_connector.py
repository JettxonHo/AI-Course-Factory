"""Public behavior tests for the GitHub Source Connector."""

import base64
from dataclasses import FrozenInstanceError
import unittest

from ai_course_factory.knowledge.github_connector import (
    MAX_API_RESPONSE_BYTES,
    MAX_FILE_COUNT,
    MAX_FILE_BYTES,
    MAX_TOTAL_BYTES,
    GitHubHTTPError,
    GitHubSourceConnector,
)
from ai_course_factory.knowledge.source import SourceAcquisitionResult, SourceConnectorFailure

COMMIT_SHA = "a" * 40
README_BLOB_SHA = "b" * 40
LESSON_BLOB_SHA = "c" * 40
GENERIC_BLOB_SHA = "d" * 40


class FixtureTransport:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def __call__(self, api_path):
        self.calls.append(api_path)
        response = self.responses[api_path]
        if isinstance(response, BaseException):
            raise response
        return response


class RaisingTransport:
    def __init__(self, error):
        self.error = error
        self.calls = []

    def __call__(self, api_path):
        self.calls.append(api_path)
        raise self.error


def file_response(path, text, blob_sha):
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return {
        "type": "file",
        "path": path,
        "sha": blob_sha,
        "size": len(text.encode("utf-8")),
        "encoding": "base64",
        "content": encoded,
    }


class GitHubSourceConnectorTests(unittest.TestCase):
    def test_valid_locator_returns_exact_commit_and_ordered_files(self):
        responses = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
            f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}": file_response(
                "README.md", "# Course\n", README_BLOB_SHA
            ),
            f"/repos/acme/course/contents/lessons/intro.md?ref={COMMIT_SHA}": file_response(
                "lessons/intro.md", "Lesson 1\n", LESSON_BLOB_SHA
            ),
        }
        transport = FixtureTransport(responses)
        connector = GitHubSourceConnector(transport=transport)

        result = connector.acquire(
            "https://github.com/acme/course",
            ["README.md", "lessons/intro.md"],
        )

        self.assertIsInstance(result, SourceAcquisitionResult)
        self.assertEqual(result.repository_url, "https://github.com/acme/course")
        self.assertEqual(result.repository_identity, "acme/course")
        self.assertEqual(result.commit_sha, COMMIT_SHA)
        self.assertEqual([item.path for item in result.files], ["README.md", "lessons/intro.md"])
        self.assertEqual([item.text for item in result.files], ["# Course\n", "Lesson 1\n"])
        self.assertEqual(
            transport.calls,
            [
                "/repos/acme/course",
                "/repos/acme/course/commits?sha=main&per_page=1",
                f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}",
                f"/repos/acme/course/contents/lessons/intro.md?ref={COMMIT_SHA}",
            ],
        )

    def test_invalid_locator_and_unsafe_paths_fail_before_transport(self):
        transport = FixtureTransport({})
        connector = GitHubSourceConnector(transport=transport)

        invalid_locators = (
            "http://github.com/acme/course",
            "https://api.github.com/repos/acme/course",
            "https://user:pass@github.com/acme/course",
            "https://github.com:443/acme/course",
            "https://github.com:not-a-port/acme/course",
            "https://github.com/acme/course?ref=main",
            "https://github.com/acme/course#readme",
            "https://github.com/acme/course/extra",
            "https://github.com/acme/course/",
        )
        for locator in invalid_locators:
            with self.subTest(locator=locator):
                failure = connector.acquire(locator, ["README.md"])
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, "INVALID_REPOSITORY_LOCATOR")
        self.assertEqual(transport.calls, [])

        invalid_paths = (
            ["/README.md"],
            ["../README.md"],
            ["lessons/../README.md"],
            ["lessons\\intro.md"],
            ["README.md", "README.md"],
            [""],
        )
        for paths in invalid_paths:
            with self.subTest(paths=paths):
                failure = connector.acquire("https://github.com/acme/course", paths)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, "INVALID_PATHS")
        self.assertEqual(transport.calls, [])
        too_many = connector.acquire(
            "https://github.com/acme/course", [f"file-{index}.md" for index in range(MAX_FILE_COUNT + 1)]
        )
        self.assertEqual(too_many.kind, "validation")
        self.assertEqual(too_many.code, "FILE_COUNT_LIMIT")
        self.assertEqual(transport.calls, [])

    def test_missing_and_malformed_responses_fail_atomically_without_partial_files(self):
        missing_repository = GitHubSourceConnector(transport=RaisingTransport(GitHubHTTPError(404))).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertIsInstance(missing_repository, SourceConnectorFailure)
        self.assertEqual(missing_repository.kind, "source_access")
        self.assertEqual(missing_repository.code, "REPOSITORY_NOT_FOUND")

        missing_commit = GitHubSourceConnector(
            transport=FixtureTransport(
                {
                    "/repos/acme/course": {"default_branch": "main"},
                    "/repos/acme/course/commits?sha=main&per_page=1": GitHubHTTPError(404),
                }
            )
        ).acquire("https://github.com/acme/course", ["README.md"])
        self.assertEqual(missing_commit.kind, "source_access")
        self.assertEqual(missing_commit.code, "COMMIT_NOT_FOUND")

        missing_file = GitHubSourceConnector(
            transport=FixtureTransport(
                {
                    "/repos/acme/course": {"default_branch": "main"},
                    "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
                    f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}": GitHubHTTPError(404),
                }
            )
        ).acquire("https://github.com/acme/course", ["README.md"])
        self.assertEqual(missing_file.kind, "source_access")
        self.assertEqual(missing_file.code, "FILE_NOT_FOUND")

        malformed_repository = GitHubSourceConnector(transport=FixtureTransport({"/repos/acme/course": b"not-json"}))
        malformed = malformed_repository.acquire("https://github.com/acme/course", ["README.md"])
        self.assertEqual(malformed.code, "MALFORMED_RESPONSE")

        malformed_commit_transport = FixtureTransport(
            {
                "/repos/acme/course": {"default_branch": "main"},
                "/repos/acme/course/commits?sha=main&per_page=1": [{"not_sha": "x"}],
            }
        )
        malformed_commit = GitHubSourceConnector(transport=malformed_commit_transport).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(malformed_commit.code, "MALFORMED_COMMIT_RESPONSE")

        common = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
        }
        malformed_file = dict(common)
        malformed_file[f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}"] = {
            "type": "file",
            "path": "README.md",
            "sha": README_BLOB_SHA,
            "size": 2,
            "encoding": "base64",
            "content": "%%%",
        }
        invalid_base64 = GitHubSourceConnector(transport=FixtureTransport(malformed_file)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(invalid_base64.code, "INVALID_BASE64")

        invalid_utf8 = dict(common)
        invalid_utf8[f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}"] = {
            "type": "file",
            "path": "README.md",
            "sha": README_BLOB_SHA,
            "size": 1,
            "encoding": "base64",
            "content": base64.b64encode(b"\xff").decode("ascii"),
        }
        non_utf8 = GitHubSourceConnector(transport=FixtureTransport(invalid_utf8)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(non_utf8.code, "INVALID_UTF8")

        mismatch = dict(common)
        mismatch[f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}"] = file_response(
            "other.md", "content", README_BLOB_SHA
        )
        metadata_mismatch = GitHubSourceConnector(transport=FixtureTransport(mismatch)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(metadata_mismatch.code, "FILE_METADATA_MISMATCH")

        partial = dict(common)
        partial[f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}"] = file_response(
            "README.md", "valid", README_BLOB_SHA
        )
        partial[f"/repos/acme/course/contents/lessons/intro.md?ref={COMMIT_SHA}"] = {
            "type": "file",
            "path": "lessons/intro.md",
            "sha": LESSON_BLOB_SHA,
            "size": 1,
            "encoding": "base64",
            "content": "%%%",
        }
        partial_result = GitHubSourceConnector(transport=FixtureTransport(partial)).acquire(
            "https://github.com/acme/course", ["README.md", "lessons/intro.md"]
        )
        self.assertIsInstance(partial_result, SourceConnectorFailure)
        self.assertEqual(partial_result.code, "INVALID_BASE64")

    def test_commit_and_blob_identity_must_be_40_character_hex(self):
        malformed_commit = FixtureTransport(
            {
                "/repos/acme/course": {"default_branch": "main"},
                "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": "g" * 40}],
            }
        )
        commit_failure = GitHubSourceConnector(transport=malformed_commit).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(commit_failure.kind, "execution")
        self.assertEqual(commit_failure.code, "MALFORMED_COMMIT_RESPONSE")

        malformed_blob = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
            f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}": file_response(
                "README.md", "valid", "g" * 40
            ),
        }
        blob_failure = GitHubSourceConnector(transport=FixtureTransport(malformed_blob)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(blob_failure.kind, "execution")
        self.assertEqual(blob_failure.code, "FILE_METADATA_MISMATCH")

        uppercase_commit = "A" * 40
        uppercase_blob = "B" * 40
        uppercase_responses = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": uppercase_commit}],
            f"/repos/acme/course/contents/README.md?ref={uppercase_commit}": file_response(
                "README.md", "uppercase is valid", uppercase_blob
            ),
        }
        uppercase_result = GitHubSourceConnector(transport=FixtureTransport(uppercase_responses)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(uppercase_result.commit_sha, uppercase_commit)
        self.assertEqual(uppercase_result.files[0].blob_sha, uppercase_blob)

    def test_api_file_and_total_content_limits_fail_closed(self):
        oversized_api = GitHubSourceConnector(
            transport=FixtureTransport({"/repos/acme/course": b"x" * (MAX_API_RESPONSE_BYTES + 1)})
        ).acquire("https://github.com/acme/course", ["README.md"])
        self.assertEqual(oversized_api.kind, "execution")
        self.assertEqual(oversized_api.code, "API_RESPONSE_TOO_LARGE")

        oversized_file = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
            f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}": file_response(
                "README.md", "x" * (MAX_FILE_BYTES + 1), README_BLOB_SHA
            ),
        }
        file_failure = GitHubSourceConnector(transport=FixtureTransport(oversized_file)).acquire(
            "https://github.com/acme/course", ["README.md"]
        )
        self.assertEqual(file_failure.kind, "execution")
        self.assertEqual(file_failure.code, "FILE_CONTENT_TOO_LARGE")

        paths = [f"lessons/{index}.md" for index in range(5)]
        oversized_total = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
        }
        for path in paths:
            oversized_total[f"/repos/acme/course/contents/{path}?ref={COMMIT_SHA}"] = file_response(
                path, "x" * MAX_FILE_BYTES, GENERIC_BLOB_SHA
            )
        total_failure = GitHubSourceConnector(transport=FixtureTransport(oversized_total)).acquire(
            "https://github.com/acme/course", paths
        )
        self.assertEqual(total_failure.kind, "execution")
        self.assertEqual(total_failure.code, "TOTAL_CONTENT_TOO_LARGE")
        self.assertGreater(MAX_TOTAL_BYTES, MAX_FILE_BYTES)

    def test_transport_failure_is_normalized_without_raw_exception_details(self):
        transport = RaisingTransport(RuntimeError("token=secret raw response body"))
        failure = GitHubSourceConnector(transport=transport).acquire(
            "https://github.com/acme/course", ["README.md"]
        )

        self.assertIsInstance(failure, SourceConnectorFailure)
        self.assertEqual(failure.kind, "source_access")
        self.assertEqual(failure.code, "TRANSPORT_ERROR")
        self.assertNotIn("secret", failure.message)
        self.assertNotIn("raw response", failure.message)

    def test_result_is_immutable_and_equivalent_repeat_has_no_artifact_side_effect(self):
        responses = {
            "/repos/acme/course": {"default_branch": "main"},
            "/repos/acme/course/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
            f"/repos/acme/course/contents/README.md?ref={COMMIT_SHA}": file_response(
                "README.md", "Do not execute this text", README_BLOB_SHA
            ),
        }
        transport = FixtureTransport(responses)
        connector = GitHubSourceConnector(transport=transport)

        first = connector.acquire("https://github.com/acme/course", ["README.md"])
        repeated = connector.acquire("https://github.com/acme/course", ["README.md"])

        self.assertEqual(first, repeated)
        self.assertIsNot(first, repeated)
        self.assertEqual(first.files[0].text, "Do not execute this text")
        with self.assertRaises(FrozenInstanceError):
            first.files[0].text = "changed"
        with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
            first.files += (first.files[0],)
        self.assertEqual(len(transport.calls), 6)
