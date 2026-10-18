# Official Competition Requirements — Checked 2026-10-18

This is a public-source review. The authenticated event-specific submission form was not accessed; its extra mandatory questions, field limits, attachment settings and private judge fields remain unverified. No entry was created or submitted.

## Deadline

The official [schedule](https://opencv26.devpost.com/details/dates) closes submissions on **October 26, 2026, 23:45 PDT**, equivalent to **October 27, 2026, 03:45 America/Fortaleza (UTC−03)**. The [overview](https://opencv26.devpost.com/) prose instead gives 23:59 Pacific, fourteen minutes later. Treat the earlier schedule cutoff as the deadline unless organizers clarify. Suggested internal target: October 26 at 20:00 Fortaleza, leaving time for review. Judging runs October 27–November 9; an availability plan must cover judge access rather than just submission day.

## Required deliverables and project evidence

Public [competition requirements](https://opencv26.devpost.com/): substantive OpenCV 5 processing; a meaningful AWS component; technical report; judge-accessible code; pinned dependencies and build/deploy/test instructions; architecture diagram; working endpoint or arranged live screen-share; evaluation with limitations; public/unlisted video up to five minutes showing team, application, architecture and results.

| Deliverable | FloodLens assessment / remaining work |
| --- | --- |
| OpenCV 5 | Pinned direct dependency and concrete decoding/mask code found; the authenticated judge deployment completed real inference on AWS on 2026-10-17. Recheck after final reactivation before judging. |
| AWS | Historical October 13 storage-enabled test documented; the final Vercel → Tailscale Funnel → ECS/Fargate → FloodLens API judge route was validated end-to-end on 2026-10-17, then intentionally scaled to zero. |
| Report and diagram | Revised report and architecture are published on PR #4's review branch; use an immutable link to the approved final commit in submission material. |
| Source and instructions | PR #4 is readable and contains the authenticated-demo safeguards; `main` does not yet include them. The deployed task/sidecar evidence is documented, but a sanitized checked-in task definition is not required to claim that the validated deployment occurred. |
| Dependency reproducibility | Direct packages are pinned, but base image, apt, transitive packages and Chart.js are not fully locked; this residual limitation is documented. |
| Judge access | External HTTPS, Basic Auth and real inference were validated on 2026-10-17. The service is intentionally at Desired=0 after testing; reactivate and repeat one external authenticated inference before the judge window. |
| Video | Complete recording script prepared; actual recording and hosting URL pending. |
| Evaluation | Frozen 20-video confusion matrix and all five metrics preserved. |

The 2026-10-17 deployment validation used ECS task definition `floodlens-task:5`, an application image pinned to ECR digest `sha256:74eba2477e09342edb873ba4f5e879df05e9399dc33267834598d70e17d72fa2`, Tailscale Funnel HTTPS, Basic Auth, SSM SecureString secret references, `FORWARDED_ALLOW_IPS=127.0.0.1`, and no general public inbound TCP 8000. The service was subsequently observed at Desired=0, Running=0, Pending=0 to stop continuous Fargate task usage. See [judge access and deployment evidence](judge_access_plan.md).

## Devpost fields

The [official Devpost form documentation](https://help.devpost.com/article/145-how-do-i-set-up-the-submission-period) marks name, tagline (140 characters), description and terms acceptance as standard mandatory fields. It also lists technologies, teammates, try-it links, images and video; organizers can add required event-specific fields. YouTube/Vimeo links are supported. Where file uploads are enabled, the documented limit is one file up to 35 MB. These platform defaults do not prove this event's complete form schema.

| Field / item to map in the actual form | Prepared value or next action |
| --- | --- |
| Name | FloodLens AI |
| Tagline / description / technologies | Copy from submission_devpost_draft.md |
| Team / representative | Confirm actual participants and eligibility in account; do not invent teammates |
| Try-it link | Landing page followed by the authenticated judge demo. Reactivate and revalidate ECS before the judge-access window. |
| Repository | Provide the reviewed branch or an approved immutable commit; do not imply PR #4 was merged while it remains draft/unmerged. |
| Report / diagram | Use the approved files or reachable immutable URLs according to the actual form. |
| Video | Insert the real hosted video URL after recording. |
| Gallery | Follow the screenshot checklist; number/size requirements remain unverified until the authenticated form can be inspected. |
| Private judge information | Confirm visibility before entering credentials; do not assume a public field is private. |
| Additional questions / terms | Owner reviews the actual form and accepts terms personally when ready; no submission has been performed. |

## Rules and divergences

The [official rules](https://opencv26.devpost.com/rules) require appropriate rights to submitted material and truthful capability claims. Organizers receive broad reuse rights over submitted materials; merely linked private assets are distinguished from submitted assets. Existing unresolved data/model provenance is not cleared by withholding weights. Review it before publication.

Overall awards do not require COOL or an agentic system. FloodLens should not claim those optional paths without the corresponding implemented evidence. The overview age summary and detailed rules differ; confirm team eligibility through the official form rather than inferring from either summary alone.

The earlier documentation review contained stale statements that the final AWS/Tailscale route had not been validated. Those statements were reconciled after the successful 2026-10-17 deployment session. The remaining practical submission items are: record and host the final video; capture approved screenshots; complete rights/media review; inspect the authenticated Devpost form and verify any private credential field; reactivate and revalidate the judge route for the judging window; account for ephemeral Tailscale identity after full task replacement; and keep the unresolved lack of hard cancellation for a stuck native decoder/model call documented.
