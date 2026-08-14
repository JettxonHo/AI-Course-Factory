from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import parse_qs, urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from jinja2 import Environment, FileSystemLoader
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from ai_course_factory.application import ApplicationResult, CourseFactoryApplication
from ai_course_factory.application.facade import REPOSITORY_URL
from ai_course_factory.production import GPTSoVITSConfiguration, GPT_SOVITS_REFERENCE_TRANSCRIPT, LocalNarrationRenderer


_PACKAGE_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _PACKAGE_DIR / "templates"
_STATIC_DIR = _PACKAGE_DIR / "static"
_MAX_FORM_BYTES = 8 * 1024
_MAX_FORM_VALUE = 128
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_FORM_ACTIONS = {
    "approve_script",
    "revise_script",
    "reject_script",
    "advance_planning",
    "approve_storyboard",
    "reject_storyboard",
    "prepare_handoff_package",
    "approve_budget",
    "produce_offline",
    "approve_final",
    "reject_final",
    "replace_scene",
    "export_package",
    "open_final",
}
_SCENE_IDS = {f"scene-{index}" for index in range(1, 7)}


class _FormError(ValueError):
    pass


def _templates() -> Jinja2Templates:
    # Explicit autoescape keeps source, finding, context and failure text inert.
    environment = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=True)
    return Jinja2Templates(env=environment)


def _safe_result_message(result: ApplicationResult | None) -> str | None:
    if result is None or result.status == "success":
        return None
    return result.error_message or "That action could not be completed. The current task state was preserved."


def _form_values(raw: bytes, allowed: set[str]) -> dict[str, str]:
    if len(raw) > _MAX_FORM_BYTES:
        raise _FormError
    try:
        decoded = raw.decode("utf-8")
        values = parse_qs(decoded, keep_blank_values=True, strict_parsing=True)
    except (UnicodeDecodeError, ValueError):
        raise _FormError from None
    if set(values) - allowed or any(len(items) != 1 for items in values.values()):
        raise _FormError
    result: dict[str, str] = {}
    for key, items in values.items():
        value = items[0]
        if len(value) > _MAX_FORM_VALUE or any(ord(char) < 32 and char not in "\t" for char in value):
            raise _FormError
        result[key] = value
    return result


def _same_loopback_origin(request: Request) -> bool:
    """Allow local mutation forms only from this exact loopback origin."""
    host = request.headers.get("host")
    origin = request.headers.get("origin")
    if not host or any(ord(char) <= 0x20 or ord(char) == 0x7F for char in host):
        return False
    try:
        parsed_host = urlsplit(f"//{host}")
        if (
            parsed_host.hostname not in _LOOPBACK_HOSTS
            or parsed_host.username is not None
            or parsed_host.password is not None
            or parsed_host.path
            or parsed_host.query
            or parsed_host.fragment
        ):
            return False
        parsed_host.port
    except (TypeError, ValueError):
        return False
    if origin is not None:
        if not origin or any(ord(char) <= 0x20 or ord(char) == 0x7F for char in origin):
            return False
        try:
            parsed_origin = urlsplit(origin)
        except (TypeError, ValueError):
            return False
        return (
            parsed_origin.scheme == request.url.scheme
            and parsed_origin.netloc == host
            and parsed_origin.username is None
            and parsed_origin.password is None
            and not parsed_origin.path
            and not parsed_origin.query
            and not parsed_origin.fragment
        )
    if (
        request.headers.get("sec-fetch-site") == "same-origin"
        and request.headers.get("sec-fetch-mode") in {None, "navigate"}
    ):
        return True
    referer = request.headers.get("referer")
    if not referer or any(ord(char) <= 0x20 or ord(char) == 0x7F for char in referer):
        return False
    try:
        parsed_referer = urlsplit(referer)
    except (TypeError, ValueError):
        return False
    return (
        parsed_referer.scheme == request.url.scheme
        and parsed_referer.netloc == host
        and parsed_referer.username is None
        and parsed_referer.password is None
    )


def _failure_page(
    templates: Jinja2Templates,
    request: Request,
    view_name: str,
    result: ApplicationResult | None,
    *,
    source_required: bool = False,
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        view_name,
        {
            "request": request,
            "view": result.view if result else None,
            "message": _safe_result_message(result),
            "source_required": source_required,
            "repository_url": REPOSITORY_URL,
        },
        status_code=400,
    )


def create_app(
    data_dir: str | Path | None = None,
    *,
    application: CourseFactoryApplication | None = None,
    source_connector: object | None = None,
    visual_import_dir: str | Path | None = None,
    tts_configuration: GPTSoVITSConfiguration | None = None,
    local_narration_renderer: LocalNarrationRenderer | None = None,
) -> FastAPI:
    """Create the local workspace app with one durable facade instance."""
    configured_dir = data_dir or os.environ.get("AI_COURSE_FACTORY_DATA_DIR") or ".ai-course-factory"
    templates = _templates()
    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        yield
        close = getattr(_app.state.course_factory, "close", None)
        if callable(close):
            close()

    app = FastAPI(title="AI Course Factory Offline Workspace", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    # Construct lazily in the serving thread.  SQLite repositories intentionally
    # belong to one app thread, while TestClient and Uvicorn may start serving
    # on a different thread from the caller that built the ASGI app.
    app.state.course_factory = application
    app.state.course_factory_data_dir = configured_dir
    app.state.course_factory_source_connector = source_connector
    app.state.course_factory_visual_import_dir = visual_import_dir if visual_import_dir is not None else os.environ.get("AI_COURSE_FACTORY_VISUAL_IMPORT_DIR")
    app.state.course_factory_tts_configuration = tts_configuration
    app.state.course_factory_local_narration_renderer = local_narration_renderer
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not _same_loopback_origin(request):
            response = HTMLResponse("Request unavailable.", status_code=400)
        else:
            try:
                response = await call_next(request)
            except Exception:
                response = HTMLResponse("Request unavailable.", status_code=500)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; style-src 'self'; media-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        response.headers.setdefault("Cache-Control", "no-store")
        return response

    def facade() -> CourseFactoryApplication:
        if app.state.course_factory is None:
            app.state.course_factory = CourseFactoryApplication(
                app.state.course_factory_data_dir,
                source_connector=app.state.course_factory_source_connector,
                visual_import_dir=app.state.course_factory_visual_import_dir,
                tts_configuration=app.state.course_factory_tts_configuration,
                local_narration_renderer=app.state.course_factory_local_narration_renderer,
            )
        return app.state.course_factory

    @app.get("/", response_class=HTMLResponse, name="start")
    async def start_view(request: Request) -> Response:
        try:
            result = facade().create_or_open()
        except Exception:
            result = None
        if result is None or result.status != "success":
            if result is not None and result.status == "source_required":
                return templates.TemplateResponse(
                    request,
                    "start.html",
                    {"request": request, "view": None, "message": None, "source_required": True, "repository_url": REPOSITORY_URL},
                )
            return _failure_page(templates, request, "start.html", result)
        return templates.TemplateResponse(request, "start.html", {"request": request, "view": result.view, "message": None, "source_required": False, "repository_url": REPOSITORY_URL})

    @app.post("/start/source", response_class=HTMLResponse, name="source_start")
    async def source_start(request: Request) -> Response:
        try:
            values = _form_values(await request.body(), {"repository_url"})
            repository_url = values.get("repository_url", "")
        except _FormError:
            invalid = ApplicationResult(
                "failure", None, "INVALID_REPOSITORY_URL", "Enter the supported public GitHub repository URL and retry."
            )
            return _failure_page(templates, request, "start.html", invalid, source_required=True)
        try:
            result = facade().start_source(repository_url)
        except Exception:
            failed = ApplicationResult(
                "failure", None, "SOURCE_ACQUISITION_FAILED", "GitHub source acquisition failed; check connectivity and retry."
            )
            return _failure_page(templates, request, "start.html", failed, source_required=True)
        if result.status != "success":
            return _failure_page(templates, request, "start.html", result, source_required=True)
        return RedirectResponse("/", status_code=303)

    @app.post("/start/script", response_class=HTMLResponse, name="script_decision")
    async def script_decision(request: Request) -> Response:
        try:
            values = _form_values(await request.body(), {"action", "decision_context"})
            action = values.get("action")
            if action not in {"approve_script", "revise_script", "reject_script"}:
                raise _FormError
            facade().create_or_open()
            normalized_action = {"approve_script": "approve", "revise_script": "revise", "reject_script": "reject"}[action]
            result = facade().submit_script_decision(normalized_action, decision_context=values.get("decision_context", ""))
        except _FormError:
            return _failure_page(templates, request, "start.html", None)
        except Exception:
            return _failure_page(templates, request, "start.html", None)
        if result.status != "success":
            return _failure_page(templates, request, "start.html", result)
        if result.view is not None and result.view.stage == "script_review":
            return RedirectResponse("/", status_code=303)
        return RedirectResponse("/review", status_code=303)

    @app.get("/review", response_class=HTMLResponse, name="review")
    async def review_view(request: Request) -> Response:
        try:
            result = facade().inspect()
        except Exception:
            result = None
        if result is None or result.status != "success":
            return _failure_page(templates, request, "review.html", result)
        return templates.TemplateResponse(request, "review.html", {"request": request, "view": result.view, "message": None})

    @app.post("/review/action", response_class=HTMLResponse, name="review_action")
    async def review_action(request: Request) -> Response:
        try:
            values = _form_values(await request.body(), {"action", "decision_context"})
            action = values.get("action")
            if action not in _FORM_ACTIONS:
                raise _FormError
            current = facade().inspect()
            if current.status != "success" or current.view is None:
                return _failure_page(templates, request, "review.html", current)
            if action == "advance_planning" and current.view.stage == "planning":
                result = facade().advance_planning()
            elif action == "approve_storyboard" and (
                current.view.stage == "planning" and current.view.pending_action == "approve_storyboard"
                or current.view.stage == "handoff_readiness" and current.view.pending_action is None
            ):
                result = facade().submit_storyboard_decision("approve", decision_context=values.get("decision_context", ""))
            elif action == "reject_storyboard" and current.view.stage == "planning" and current.view.pending_action == "approve_storyboard":
                result = facade().submit_storyboard_decision(
                    "reject",
                    decision_context=values.get("decision_context", ""),
                )
            elif action == "prepare_handoff_package" and current.view.stage == "handoff_readiness":
                result = facade().prepare_handoff_package()
            elif action == "approve_budget" and current.view.stage == "budget_review":
                result = facade().submit_budget_decision("approve")
            elif action == "produce_offline" and current.view.stage == "production":
                result = facade().produce_offline()
            elif action == "open_final" and current.view.stage == "final_review":
                return RedirectResponse("/final", status_code=303)
            else:
                raise _FormError
        except _FormError:
            return _failure_page(templates, request, "review.html", None)
        except Exception:
            return _failure_page(templates, request, "review.html", None)
        if result.status != "success":
            return _failure_page(templates, request, "review.html", result)
        if result.view is not None and result.view.stage == "final_review":
            return RedirectResponse("/final", status_code=303)
        return RedirectResponse("/review", status_code=303)

    @app.get("/final", response_class=HTMLResponse, name="final")
    async def final_view(request: Request) -> Response:
        try:
            result = facade().inspect()
        except Exception:
            result = None
        if result is None or result.status != "success":
            return _failure_page(templates, request, "final.html", result)
        return templates.TemplateResponse(request, "final.html", {"request": request, "view": result.view, "message": None})

    @app.post("/final/action", response_class=HTMLResponse, name="final_action")
    async def final_action(request: Request) -> Response:
        try:
            values = _form_values(await request.body(), {"action", "scene_id", "decision_context"})
            action = values.get("action")
            if action not in _FORM_ACTIONS:
                raise _FormError
            if action in {"approve_final", "reject_final"}:
                result = facade().submit_final_decision("approve" if action == "approve_final" else "reject", decision_context=values.get("decision_context", ""))
            elif action == "replace_scene" and values.get("scene_id") in _SCENE_IDS:
                result = facade().replace_scene(values["scene_id"])
            elif action == "export_package":
                result = facade().export_package()
            else:
                raise _FormError
        except _FormError:
            return _failure_page(templates, request, "final.html", None)
        except Exception:
            return _failure_page(templates, request, "final.html", None)
        if result.status != "success":
            return _failure_page(templates, request, "final.html", result)
        return RedirectResponse("/final", status_code=303)

    @app.get("/media/{kind}", name="download")
    async def download(kind: str) -> Response:
        if kind not in {"video", "subtitle", "package", "handoff_package"}:
            return Response("Not found.", status_code=404, media_type="text/plain")
        try:
            download = facade().read_output(kind)
        except Exception:
            download = None
        if download is None:
            return Response("Not found.", status_code=404, media_type="text/plain")
        return Response(
            download.content,
            media_type=download.media_type,
            headers={"Content-Disposition": f"inline; filename=\"{download.filename}\"" if kind not in {"package", "handoff_package"} else f"attachment; filename=\"{download.filename}\""},
        )

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Course Factory offline workspace")
    parser.add_argument("--data-dir", required=True, help="explicit durable local data directory")
    parser.add_argument("--visual-import-dir", required=False, help="explicit directory containing scene-1.png through scene-6.png")
    parser.add_argument("--tts-external-python", required=False)
    parser.add_argument("--tts-repository-root", required=False)
    parser.add_argument("--tts-repository-commit", required=False)
    parser.add_argument("--tts-inference-script", required=False)
    parser.add_argument("--tts-config", required=False)
    parser.add_argument("--tts-gpt-model", required=False)
    parser.add_argument("--tts-sovits-model", required=False)
    parser.add_argument("--tts-reference-audio", required=False)
    parser.add_argument("--tts-reference-transcript", default=GPT_SOVITS_REFERENCE_TRANSCRIPT)
    parser.add_argument("--tts-model-identifier", default="gsv-v2final-pretrained")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    import uvicorn

    tts_values = (
        args.tts_external_python, args.tts_repository_root, args.tts_repository_commit,
        args.tts_inference_script, args.tts_config, args.tts_gpt_model,
        args.tts_sovits_model, args.tts_reference_audio,
    )
    tts_configuration = None
    if any(value is not None for value in tts_values):
        tts_configuration = GPTSoVITSConfiguration(
            external_python=args.tts_external_python or "",
            repository_root=args.tts_repository_root or "",
            repository_commit=args.tts_repository_commit or "",
            inference_script=args.tts_inference_script or "",
            tts_config=args.tts_config or "",
            gpt_model=args.tts_gpt_model or "",
            sovits_model=args.tts_sovits_model or "",
            reference_audio=args.tts_reference_audio or "",
            reference_transcript=args.tts_reference_transcript,
            model_identifier=args.tts_model_identifier,
        )
    uvicorn.run(create_app(args.data_dir, visual_import_dir=args.visual_import_dir, tts_configuration=tts_configuration), host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":  # pragma: no cover
    main()
