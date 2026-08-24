"""Test-only schema-1 fixtures for readable FAST-MVP v1.1 states.

H1 intentionally changes the fresh path.  These helpers build the historical
skip-to-budget state through the real Artifact/Decision boundaries so legacy
facade/media tests continue to exercise restart compatibility without adding a
production legacy API or assigning a Scene Generation Contract to v1.1 data.
"""

from __future__ import annotations

from ai_course_factory.agents import ContentAgent, ContentTaskContext, EpisodeTemplateConstraint, KnowledgeAgent, KnowledgeTaskContext, ProductionAgent
from ai_course_factory.application.facade import CREATOR_ID, TASK_ID, THREAD_ID, _OfflineRuntime, _State
from ai_course_factory.artifacts import ScriptDecisionRecord, StoryboardDecisionBoundary, StoryboardDecisionRecord
from ai_course_factory.application.media_task import TaskMediaProjectionService
from ai_course_factory.application.script_review import ScriptReviewApplicationService
from ai_course_factory.artifacts import ScriptDecisionBoundary
from ai_course_factory.production import BudgetModule, RetryPolicy
from ai_course_factory.workflow import ScriptReviewWorkflow


def seed_legacy_budget_review(app):
    """Return ``app`` reopened at the historical schema-1 budget gate."""

    opened = app.create_or_open()
    if opened.status == "source_required":
        raise AssertionError("source must be initialized before seeding")
    if "script" not in (app._load_state().refs if app._load_state() is not None else {}):
        seed_legacy_script_review(app)
    if app.submit_script_decision("approve").status != "success":
        raise AssertionError("Script approval failed")
    planning = app.advance_planning()
    if planning.status != "success":
        raise AssertionError("H1 planning failed")
    state = app._load_state()
    if state is None:
        raise AssertionError("state missing")
    script_reference = state.refs["script"]
    character_reference = state.refs["character"]
    storyboard_reference = state.refs["storyboard"]
    script = app.artifacts.get(script_reference)
    character = app.artifacts.get(character_reference)
    storyboard = app.artifacts.get(storyboard_reference)
    script_decision = app.script_decisions.get(state.decision_ids["script"])
    if not isinstance(script_decision, ScriptDecisionRecord):
        raise AssertionError("Script decision missing")
    storyboard_decision = StoryboardDecisionBoundary(app.storyboard_decisions).decide(
        storyboard_reference,
        storyboard,
        review_enabled=False,
        decision_id=f"decision:storyboard:skip:v{storyboard_reference.version}",
        task_id=TASK_ID,
        thread_id=THREAD_ID,
        creator_id=CREATOR_ID,
        action="skip",
    )
    if not isinstance(storyboard_decision, StoryboardDecisionRecord):
        raise AssertionError("legacy Storyboard skip failed")
    production = ProductionAgent(_OfflineRuntime())
    timeline_candidate = production.plan_timeline(
        script_reference,
        script,
        script_decision,
        character_reference,
        character,
        storyboard_reference,
        storyboard,
        storyboard_decision,
        timeline_identity="timeline:episode-1",
        timeline_commit_id="timeline-1",
    )
    timeline_reference = app.artifacts.commit(timeline_candidate)
    timeline = app.artifacts.get(timeline_reference)
    request_candidate = production.plan_request(
        script_reference,
        script,
        script_decision,
        character_reference,
        character,
        storyboard_reference,
        storyboard,
        storyboard_decision,
        timeline_reference,
        timeline,
        request_identity="production-request:episode-1",
        request_commit_id="production-request-1",
    )
    request_reference = app.artifacts.commit(request_candidate)
    request = app.artifacts.get(request_reference)
    budget_reference = app.artifacts.commit(
        BudgetModule.estimate(
            request_reference,
            request,
            price_snapshot=app._price_snapshot(request_reference, request),
            retry_policy=RetryPolicy(2),
            budget_identity="budget:episode-1",
            budget_commit_id="budget-1",
        )
    )
    media = TaskMediaProjectionService(app.artifacts, app.media_repository)
    created = media.create(TASK_ID, "media:create", request_reference)
    if created.status != "success":
        raise AssertionError("legacy media projection failed")
    refs = {
        **state.refs,
        "timeline": timeline_reference,
        "production_request": request_reference,
        "production_budget": budget_reference,
    }
    legacy = _State(
        TASK_ID,
        "budget_review",
        "approve_budget",
        refs,
        {**state.decision_ids, "storyboard": storyboard_decision.decision_id},
        None,
        None,
        None,
        None,
        None,
        state.replacement_done,
        state.visual_mode,
        state.tts_mode,
    )
    if "scene_generation_contract" in legacy.refs:
        raise AssertionError("legacy v1.1 fixture must not carry a Scene Generation Contract")
    app._save_state(legacy)
    restored = app._load_state()
    if restored is None or restored.stage != "budget_review" or restored.pending_action != "approve_budget" or "scene_generation_contract" in restored.refs:
        raise AssertionError("legacy v1.1 budget checkpoint did not persist as schema-1 state")
    return app


def seed_legacy_script_review(app):
    """Build the historical v1.1 Script lineage explicitly for compatibility tests."""

    state = app._load_state()
    if state is None or "source" not in state.refs:
        raise AssertionError("source must be initialized before seeding legacy Script")
    if "script" in state.refs:
        return app
    prepared = app.workspace.prepare(TASK_ID)
    if not hasattr(prepared, "task_id"):
        raise AssertionError("legacy workspace could not be prepared")
    source_reference = state.refs["source"]
    source = app.artifacts.get(source_reference)
    runtime = _OfflineRuntime()
    knowledge_candidate = KnowledgeAgent(runtime).invoke(
        source_reference, source,
        context=KnowledgeTaskContext("AI-For-Beginners", "Lesson 1", "English", "adult AI beginners"),
        identity="knowledge:episode-1", commit_id="knowledge:episode-1", knowledge_boundary="traceable-source-only",
    )
    knowledge_reference = app.artifacts.commit(knowledge_candidate)
    knowledge = app.artifacts.get(knowledge_reference)
    context = ContentTaskContext("adult AI beginners", "小土豆学 AI", 1, "AI不是魔法", "Simplified Chinese", "Explain why AI is not magic.")
    template = EpisodeTemplateConstraint(6, 60, "9:16")
    plans = ContentAgent(runtime).plan(
        knowledge_reference, knowledge, context=context, template=template,
        course_identity="course-plan:episode-1", episode_identity="episode-plan:episode-1",
        course_commit_id="course-plan:episode-1", episode_commit_id="episode-plan:episode-1",
    )
    course_reference = app.artifacts.commit(plans.course)
    episode_reference = app.artifacts.commit(plans.episode)
    script_candidate = ContentAgent(runtime).script(
        knowledge_reference, knowledge, course_reference, app.artifacts.get(course_reference),
        episode_reference, app.artifacts.get(episode_reference), context=context, template=template,
        script_identity="script:episode-1", script_commit_id="script:episode-1",
    )
    script_reference = app.artifacts.commit(script_candidate)
    result = ScriptReviewApplicationService(
        app.artifacts, ScriptDecisionBoundary(app.script_decisions), ScriptReviewWorkflow(app.artifacts, app.checkpoints)
    ).start(TASK_ID, f"{THREAD_ID}-v{script_reference.version}", script_reference)
    if result.status == "failure":
        raise AssertionError(result.error_message)
    app._save_state(_State(
        TASK_ID, "script_review", "approve_script",
        {"source": source_reference, "knowledge": knowledge_reference, "course_plan": course_reference, "episode_plan": episode_reference, "script": script_reference},
        {}, None, None, None, None, None, state.replacement_done, state.visual_mode, state.tts_mode,
    ))
    return app
