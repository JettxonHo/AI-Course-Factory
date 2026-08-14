# AI Course Factory

AI Course Factory 是一个本地优先的 AI 教育短视频生产应用。它把公开 GitHub 仓库中的可追溯知识，转换为经过人工审核的脚本、生产计划、视频和可导出的发布包。

当前代码已具备从 Source 到本地 Publish Package 的大部分离线后端能力；获批的 FAST-MVP 方向是把这些能力尽快接成可操作的本地产品：

```text
Public GitHub source
  -> grounded Script + human review
  -> production plan + budget approval
  -> Visual/TTS or explicit Desktop ImageGen import + FFmpeg
  -> final review + local export
```

本地 Web 工作台已完成 F1 facade、F2A Desktop ImageGen 外部图片导入、F2B 本地 GPT-SoVITS v2 TTS 和 F2.5 Warm Editorial 三页体验。Issue #123 / PR #124 的媒体证据因 Fixture Source 仅保留为部分历史；Issue #125 已从全新数据目录通过浏览器提交支持的公开 URL，以默认连接器获取 live GitHub source，并在同一任务完成真实本地媒体、两次重启、Scene 2 视觉替换和四文件 ZIP。该纠正候选已获主控批准合并，最终 `GOAL_APPROVED` 仍待合并后的策划复核。当前事实见 [docs/STATUS.md](docs/STATUS.md)，候选验收记录见 [F3 Acceptance Record](docs/acceptance/FAST-MVP-v1.1-F3-ACCEPTANCE.md)。

## 已验收的本地工作台

依赖安装后，可用明确的数据目录在 loopback 启动三页 server-rendered 工作台：

```bash
PYTHONPATH=src uv run python -m ai_course_factory.web --data-dir ./var/ai-course-factory
```

默认只绑定 `127.0.0.1:8000`。未配置 GPT-SoVITS 时工作台使用本地确定性 FFmpeg Fixture；配置 F2B 的显式 GPT-SoVITS 参数后，语音路径使用本地 GPT-SoVITS v2，不调用云端 Provider，视频、SRT 和最终 ZIP 只从当前 facade 状态提供。

若使用 F2A 的 Creator-supplied Desktop ImageGen 图片，必须显式传入目录；应用只接受精确的 `scene-1.png` 至 `scene-6.png`，Scene 2 替换只接受 `scene-2-replacement.png`，不会猜测 Downloads、Desktop 或“最新文件”：

```bash
PYTHONPATH=src uv run python -m ai_course_factory.web \
  --data-dir ./var/ai-course-factory \
  --visual-import-dir ./var/desktop-imagegen-assets
```

Desktop ImageGen 生成发生在应用外；导入模式的本地处理费用为 0，仍须先通过现有 Budget approval。缺失或不可解码的文件会在任何 attempt、media 或 Artifact side effect 前一次性报告安全的文件名。

配置 F2B 本地 GPT-SoVITS 时，必须显式提供外部 Python 3.11、官方仓库/commit、v2 推理脚本与配置、精确模型文件、Serena 参考音频和参考文本；应用不会扫描本机目录或使用云端凭据：

```bash
PYTHONPATH=src uv run python -m ai_course_factory.web \
  --data-dir ./var/ai-course-factory \
  --visual-import-dir ./var/desktop-imagegen-assets \
  --tts-external-python /path/to/gpt-sovits/venv/bin/python \
  --tts-repository-root /path/to/gpt-sovits/repo \
  --tts-repository-commit d523079fc05d9a8028d6085bffe4a2757c32abb6 \
  --tts-inference-script /path/to/gpt-sovits/repo/GPT_SoVITS/inference_cli.py \
  --tts-config /path/to/gpt-sovits/repo/GPT_SoVITS/configs/tts_infer.yaml \
  --tts-gpt-model /path/to/gpt-sovits/repo/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt \
  --tts-sovits-model /path/to/gpt-sovits/repo/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth \
  --tts-reference-audio /path/to/synthetic-serena-reference_000.wav \
  --tts-reference-transcript '你好，我是小土豆。今天我们一起认识人工智能。'
```

The external runtime, model cache and reference audio remain operator-owned files outside this repository; local GPT-SoVITS inference records zero external charge.

## 开始之前

Codex 和开发者按以下顺序阅读：

1. [docs/README.md](docs/README.md)
2. [GOAL.md](GOAL.md)
3. [docs/STATUS.md](docs/STATUS.md)
4. [AGENTS.md](AGENTS.md)

## 当前验证命令

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

运行要求：Python 3.12。新增依赖只在当前纵向任务确有需要时加入。

## 权威文档

- [PRD](docs/product/PRD.md)：产品必须做什么。
- [System Spec](docs/spec/SYSTEM-SPEC.md)：系统必须保持什么行为和契约。
- [Implementation Spec](docs/spec/IMPLEMENTATION-SPEC.md)：代码和运行时怎样实现这些契约。
- [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md)：Codex、Goal、Luna、Issue、PR 和验收怎样协作。

历史 Phase 文档保留为决策与交付证据，但不再作为日常开发入口。
