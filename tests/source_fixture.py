from __future__ import annotations

from collections.abc import Iterable

from ai_course_factory.knowledge import SourceAcquisitionResult, SourceConnectorFailure, SourceFile


SUPPORTED_REPOSITORY_URL = "https://github.com/microsoft/AI-For-Beginners"
REAL_SHAPED_COMMIT = "0123456789abcdef0123456789abcdef01234567"
REAL_SHAPED_BLOB = "abcdef0123456789abcdef0123456789abcdef01"
LESSON_PATH = "lessons/4-ComputerVision/06-IntroCV/README.md"
LESSON_TEXT = (
    "# Introduction to Computer Vision\n\n"
    "[Computer Vision](https://wikipedia.org/wiki/Computer_vision) is a discipline whose aim is to allow computers to gain high-level understanding of digital images.\n\n"
    "## OpenCV\n\n"
    "[OpenCV](https://opencv.org/) is considered to be the *de facto* standard for image processing. It contains a lot of useful algorithms, implemented in C++. You can call OpenCV from Python as well.\n\n"
    "### Loading Images\n\n"
    "Images in Python can be conveniently represented by NumPy arrays. For example, grayscale images with the size of 320x200 pixels would be stored in a 200x320 array, and color images of the same dimension would have shape of 200x320x3 (for 3 color channels).\n\n"
    "Traditionally, OpenCV uses BGR (Blue-Green-Red) encoding for color images, while the rest of Python tools use the more traditional RGB (Red-Green-Blue).\n\n"
    "### Image Processing\n\n"
    "Before feeding an image to a neural network, you may want to apply several pre-processing steps. OpenCV can do many things, including:\n\n"
    "* **Resizing** the image using `im = cv2.resize(im, (320,200),interpolation=cv2.INTER_LANCZOS)`\n"
    "* Changing the **brightness and contrast** of the image can be done by NumPy array manipulations, as described [in this Stackoverflow note](https://stackoverflow.com/questions/39308030/how-do-i-increase-the-contrast-of-an-image-in-python-opencv).\n"
    "* Understanding movement inside the image by using **[optical flow](https://docs.opencv.org/4.5.5/d4/dee/tutorial_optical_flow.html)**.\n\n"
    "## Examples of using Computer Vision\n\n"
    "* **Detecting motion in video using frame difference**. If the camera is fixed, then frames from the camera feed should be pretty similar to each other. Since frames are represented as arrays, just by subtracting those arrays for two subsequent frames we will get the pixel difference, which should be low for static frames, and become higher once there is substantial motion in the image.\n\n"
    "* **Detecting motion using Optical Flow**. [Optical flow](https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html) allows us to understand how individual pixels on video frames move.\n"
)


class FixtureSourceConnector:
    """Explicit test-only source boundary; production never imports this."""

    def __init__(self, failures: Iterable[SourceConnectorFailure] = ()) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.failures = list(failures)

    def acquire(self, repository_url: str, paths: list[str] | tuple[str, ...]) -> SourceAcquisitionResult | SourceConnectorFailure:
        self.calls.append((repository_url, tuple(paths)))
        if self.failures:
            return self.failures.pop(0)
        return SourceAcquisitionResult(
            repository_url=SUPPORTED_REPOSITORY_URL,
            repository_identity="microsoft/AI-For-Beginners",
            commit_sha=REAL_SHAPED_COMMIT,
            files=(SourceFile(LESSON_PATH, REAL_SHAPED_BLOB, LESSON_TEXT, len(LESSON_TEXT.encode("utf-8"))),),
            total_size_bytes=len(LESSON_TEXT.encode("utf-8")),
        )


def ensure_source(application: object) -> object:
    """Start the explicit test source when a legacy flow needs a task."""
    create_or_open = getattr(application, "create_or_open")
    result = create_or_open()
    if result.status == "source_required":
        started = application.start_source(SUPPORTED_REPOSITORY_URL)
        if started.status != "success":
            raise AssertionError(started.error_message)
        return started
    return result
