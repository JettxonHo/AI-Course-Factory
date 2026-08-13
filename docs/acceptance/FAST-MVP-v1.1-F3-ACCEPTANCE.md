# FAST-MVP v1.1 F3 Acceptance Record

## Verdict

**GOAL_APPROVED**

The main controller accepted the fixed local FAST-MVP browser Demo on 2026-08-14. The run started from a previously nonexistent data directory on `main@e155d193032aad6a9c98e1e8cbebd4e10febdbc6` and used the merged Warm Editorial three-view workspace. No product-code correction or Luna implementation task was required.

This verdict accepts a local, single-user MVP. It is not evidence of cloud Provider use, paid execution, deployment, publication, adoption, or production operations.

## Fixed acceptance inputs

- Public source: `https://github.com/microsoft/AI-For-Beginners`
- Locked source commit: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`
- Source unit: `lessons/intro.md#L1-L2`
- Visuals: the seven approved operator-owned files `scene-1.png` through `scene-6.png` plus `scene-2-replacement.png`
- TTS engine: local GPT-SoVITS v2, official repository commit `d523079fc05d9a8028d6085bffe4a2757c32abb6`
- TTS model identifier: `gsv-v2final-pretrained`
- Reference provenance: locally generated Qwen3-TTS Serena synthetic reference
- Reference transcript: `你好，我是小土豆。今天我们一起认识人工智能。`
- Runtime boundary: explicit external Python 3.11 and model cache outside this repository

The repository contains none of the input images, model weights, reference audio, generated media, ZIP, screenshots, or machine-specific absolute paths.

## Browser flow evidence

The controller completed this sequence through the three server-rendered views:

1. opened a fresh task and inspected the exact repository commit and source locator;
2. revised Script v1 with explicit context, producing the same Script identity at v2;
3. approved exact Script v2, then built the six-Scene plan;
4. inspected and approved the unchanged maximum of 18,000 micros and two attempts;
5. produced six imported visuals and six real local GPT-SoVITS narrations;
6. verified playable Video v1 and nonempty six-Scene subtitles;
7. restarted the process with all attempt, cost, media and review facts unchanged;
8. replaced only Scene 2 visual, producing Scene Clip v2 and Video v2;
9. approved exact Video v2 and exported the delivery package;
10. restarted a second time and replayed the video, subtitle and package endpoints byte-for-byte.

Script decisions bind `script:episode-1` v1 for revision and v2 for approval. The Final decision binds `media:episode-1` Video v2. Export was absent before Final approval and available only after the approval was persisted.

## Budget and local-processing evidence

- Before Budget approval: zero Budget decisions, zero Budget authorizations, zero media attempts, and no Scene Clip, Scene Audio, Subtitle, Master Audio or Video Artifact existed.
- Approved maximum: 18,000 micros and two attempts, unchanged from the fixed Demo contract.
- Initial production: exactly six `local-import-operator-declared-external-source` visual attempts and six `local-gpt-sovits-v2` voice attempts.
- Every attempt completed `succeeded` with `charged_amount_micros = 0`.
- Scene 2 visual replacement created no additional voice attempt and did not masquerade as a cloud Provider call.
- After replacement and both restarts: 12 total attempts, six voice attempts and zero total external charge.

## Media and Scene-replacement evidence

Independent FFprobe of the final Video v2 reported:

- MP4-family container;
- H.264, 540 x 960, `yuv420p`, 24/1 fps;
- AAC, 48 kHz, mono;
- one `mov_text` subtitle stream;
- exact 60-second duration.

The SRT endpoint returned HTTP 200 and six ordered, nonempty ten-second cues. Browser media state reached `readyState = 4`; keyboard playback advanced the current time. Each Scene voice file is a ten-second AAC 48 kHz mono file with non-silent signal. A separate local CPU transcription identified Chinese with probability 1.0 for all six clips and recovered the central phrase `人工智能不是魔法` from every clip.

A frame contact sheet independently showed six distinct creator-supplied visual scenes. The Scene 2 frame after replacement matches the approved replacement asset rather than the original Scene 2 image or a Fixture fallback.

The replacement preserved:

- exact Scene 2 voice attempt and `scene-2.m4a` output;
- Scene Audio v1 and Master Audio v1;
- Scene Clip v1 for Scenes 1, 3, 4, 5 and 6;
- all other voice and audio references.

Only Scene 2 Scene Clip advanced to v2 and the derived Video advanced from v1 to v2 with exact predecessor references.

## Restart, package and attribution evidence

The first restart preserved Video v1, the `final_review` gate, 12 zero-charge attempts and every visual/TTS file modification time. It performed no repeated inference or visual conversion.

The exported ZIP contains exactly, in deterministic order:

1. `video.mp4`
2. `subtitles.srt`
3. `source-attribution.json`
4. `artifact-manifest.json`

ZIP video and subtitle bytes equal the current workspace outputs. The manifest binds Final decision `decision:final:v2:approve`, Video v2, Subtitle v1 and Source Record v1. Attribution preserves the exact GitHub repository, commit and unit and adds:

- selected `scene-2-replacement.png` visual evidence;
- creator-supplied Desktop ImageGen, generated outside the application;
- local GPT-SoVITS v2 repository commit/model/runtime facts;
- the synthetic Serena reference provenance;
- `application_provider_api_call = false`;
- `external_charge_micros = 0`.

After the second restart, video, subtitle and package endpoints all returned HTTP 200 with the expected MIME types. Their bytes and the workspace media/package modification times remained unchanged; Artifact Manifest and Publish Package stayed at v1 and Video stayed at v2.

## Product-experience evidence

- The full flow used Start, Review / Produce and Final / Export; no internal facade call substituted for the browser workflow.
- Desktop review at 1440 x 900 showed the asymmetric 9:16 video and decision rail with no horizontal overflow.
- Chrome review at 375 x 812 showed the single-column layout, static mobile decision rail and no horizontal overflow.
- Stage navigation exposed completed/current state through `aria-current`; task, stage and one next action remained primary.
- Keyboard Tab reached the skip link, workspace navigation and stage track with visible solid focus; keyboard Space exercised video playback.
- Source, Budget, local attempt, zero-charge, visual and TTS provenance remained visible while raw configuration paths and internal errors did not appear.
- Screenshots and generated inspection assets remain outside the repository.

## Repository verification

The final feature branch passed:

- 37 focused web, local-import, GPT-SoVITS, facade and durable integration tests;
- the complete 414-test local regression;
- `compileall` for `src` and `tests`;
- `git diff --check` and an exact documentation-only ownership review.

The final regression was rerun quietly because the first verbose tool response was truncated before its summary could be retained. Neither repository run invokes the opt-in heavy GPT-SoVITS acceptance path. GitHub hosted checks are not claimed.

## Remaining boundary

FAST-MVP v1.1 is accepted for its fixed local Demo. Automatic cloud Visual/TTS Providers, credentials, paid usage, multiple tasks/users, authentication, deployment, publication and product adoption remain outside this Goal and are not inferred from this acceptance.
