"""Application-layer orchestration seams for the MVP vertical slice."""

from .script_review import ScriptReviewApplicationResult, ScriptReviewApplicationService
from .final_video_review import (
    FinalVideoReviewApplicationResult,
    FinalVideoReviewApplicationService,
)
from .sqlite_task import SQLiteTaskRepository
from .task import (
    InMemoryTaskRepository,
    TaskArtifactSelection,
    TaskImpact,
    TaskOperationResult,
    TaskProjectionChange,
    TaskProjectionService,
    TaskRepository,
    TaskRepositoryFailure,
    TaskSnapshot,
)
from .media_task import (
    InMemoryTaskMediaRepository,
    TaskDeliveryMediaSelection,
    TaskMediaImpact,
    TaskMediaOperationResult,
    TaskMediaProjectionChange,
    TaskMediaProjectionService,
    TaskMediaRepository,
    TaskMediaRepositoryFailure,
    TaskMediaSnapshot,
    TaskSceneMediaSelection,
)
from .sqlite_media_task import SQLiteTaskMediaRepository
from .facade import ApplicationDownload, ApplicationResult, ApplicationView, CourseFactoryApplication, SceneView

__all__ = [
    "InMemoryTaskRepository",
    "ScriptReviewApplicationResult",
    "ScriptReviewApplicationService",
    "FinalVideoReviewApplicationResult",
    "FinalVideoReviewApplicationService",
    "SQLiteTaskRepository",
    "TaskArtifactSelection",
    "TaskImpact",
    "TaskOperationResult",
    "TaskProjectionChange",
    "TaskProjectionService",
    "TaskRepository",
    "TaskRepositoryFailure",
    "TaskSnapshot",
    "InMemoryTaskMediaRepository",
    "TaskDeliveryMediaSelection",
    "TaskMediaImpact",
    "TaskMediaOperationResult",
    "TaskMediaProjectionChange",
    "TaskMediaProjectionService",
    "TaskMediaRepository",
    "TaskMediaRepositoryFailure",
    "TaskMediaSnapshot",
    "TaskSceneMediaSelection",
    "SQLiteTaskMediaRepository",
    "ApplicationResult",
    "ApplicationDownload",
    "ApplicationView",
    "CourseFactoryApplication",
    "SceneView",
]
