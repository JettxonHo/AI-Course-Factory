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


class LocalImportedVisualIntegrationTests(unittest.TestCase):
    def test_six_images_replacement_restart_and_zip_replay(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            for index, colour in enumerate(("red", "blue", "green", "yellow", "purple", "orange"), start=1):
                _write_png(imports / f"scene-{index}.png", colour)
            app = CourseFactoryApplication(root / "data", visual_import_dir=imports)
            app.create_or_open()
            app.submit_script_decision("approve")
            app.advance_planning()
            app.submit_budget_decision("approve")
            produced = app.produce_offline()
            self.assertEqual(produced.status, "success")
            before = produced.view.video_reference

            _write_png(imports / "scene-2-replacement.png", "pink")
            replaced = app.replace_scene("scene-2")
            self.assertEqual(replaced.status, "success")
            self.assertNotEqual(replaced.view.video_reference, before)
            app.close()

            resumed = CourseFactoryApplication(root / "data", visual_import_dir=imports)
            self.assertEqual(resumed.create_or_open().view.video_reference, replaced.view.video_reference)
            self.assertEqual(resumed.submit_final_decision("approve").status, "success")
            exported = resumed.export_package()
            self.assertEqual(exported.status, "success")
            package = resumed.workspace.read(exported.view.package_output)
            self.assertIsInstance(package, bytes)
            with zipfile.ZipFile(io.BytesIO(package)) as archive:
                attribution = json.loads(archive.read("source-attribution.json"))
            self.assertEqual(attribution["visual_assets"]["selected_assets"][1]["target_filename"], "scene-2-replacement.png")
            self.assertFalse(attribution["visual_assets"]["application_provider_api_call"])


if __name__ == "__main__":
    unittest.main()
