# Official Competition Requirements — Checked 2026-10-18

This is a public-source review. The authenticated event-specific submission form was not accessed; its extra mandatory questions, field limits, attachment settings and private judge fields remain unverified. No entry was created or submitted.

## Deadline

The official [schedule](https://opencv26.devpost.com/details/dates) closes submissions on **October 26, 2026, 23:45 PDT**, equivalent to **October 27, 2026, 03:45 America/Fortaleza (UTC−03)**. The [overview](https://opencv26.devpost.com/) prose instead gives 23:59 Pacific, fourteen minutes later. Treat the earlier schedule cutoff as the deadline unless organizers clarify. Suggested internal target: October 26 at 20:00 Fortaleza, leaving time for review. Judging runs October 27–November 9; an availability plan must cover judge access rather than just submission day.

## Required deliverables and project evidence

Public [competition requirements](https://opencv26.devpost.com/): substantive OpenCV 5 processing; a meaningful AWS component; technical report; judge-accessible code; pinned dependencies and build/deploy/test instructions; architecture diagram; working endpoint or arranged live screen-share; evaluation with limitations; public/unlisted video up to five minutes showing team, application, architecture and results.

| Deliverable | FloodLens assessment / remaining work |
| --- | --- |
| OpenCV 5 | Pinned direct dependency and concrete decoding/mask code found; verify actual deployed runtime |
| AWS | Historical October 13 test documented; final Funnel-to-ECS route not established by this review |
| Report and diagram | Revised proposal included; approve and link the exact published version |
| Source and instructions | PR #4 readable; main lacks its safeguards; weights excluded and sidecar deployment instructions incomplete |
| Dependency reproducibility | Direct packages pinned, but base image, apt, transitive packages and Chart.js are not fully locked |
| Judge access | Landing 200, demo 502 from review environment; authenticate and test after availability is restored |
| Video | Complete 4:40 recording script; actual recording and hosting URL pending |
| Evaluation | Frozen 20-video confusion matrix and all five metrics preserved |

## Devpost fields

The [official Devpost form documentation](https://help.devpost.com/article/145-how-do-i-set-up-the-submission-period) marks name, tagline (140 characters), description and terms acceptance as standard mandatory fields. It also lists technologies, teammates, try-it links, images and video; organizers can add required event-specific fields. YouTube/Vimeo links are supported. Where file uploads are enabled, the documented limit is one file up to 35 MB. These platform defaults do not prove this event's complete form schema.

| Field / item to map in the actual form | Prepared value or next action |
| --- | --- |
| Name | FloodLens AI |
| Tagline / description / technologies | Copy from submission_devpost_draft.md |
| Team / representative | Confirm actual participants and eligibility in account; do not invent teammates |
| Try-it link | Landing page, then authenticated demo; fix availability first |
| Repository | Provide reviewed branch or approved immutable commit; do not imply PR was merged |
| Report / diagram | Use approved files or reachable immutable URLs according to actual form |
| Video | Insert real hosted video URL after recording |
| Gallery | Follow screenshot checklist; number/size requirements not verified |
| Private judge information | Confirm visibility before entering credentials; do not assume a public field is private |
| Additional questions / terms | Owner reviews actual form and accepts terms personally when ready; no submission in this task |

## Rules and divergences

The [official rules](https://opencv26.devpost.com/rules) require appropriate rights to submitted material and truthful capability claims. Organizers receive broad reuse rights over submitted materials; merely linked private assets are distinguished from submitted assets. Existing unresolved data/model provenance is not cleared by withholding weights. Review it before publication.

Overall awards do not require COOL or an agentic system. FloodLens should not claim those optional paths without the corresponding implemented evidence. The overview age summary and detailed rules differ; confirm team eligibility through the official form rather than inferring from either summary alone.

The current material's practical divergences are recorded in [submission audit](submission_review_2026-10-18.md): stale availability language, incomplete access/deployment evidence, absent video, unresolved rights, misleading main-branch links, missing specificity in the old video script, and incomplete dependency locking.
