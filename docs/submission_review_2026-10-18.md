# FloodLens AI — Submission Review and Proposed Changes

Review date: 2026-10-18. Scope: repository documentation, PR #4, public landing/demo links, official competition pages. No commit/push, merge, Devpost edit/submission, infrastructure action, model change, training or inference was performed.

## Reviewed baseline

- Repository: https://github.com/joa0lucassi/floodlens-ai
- PR: https://github.com/joa0lucassi/floodlens-ai/pull/4 — open, draft, not merged.
- Head: `24ea9a86cf300c1f268ccc82ef0b98d9f15a8f77`.
- Base main: `d48358ed1abfc4956e32035a95f23c8f9d093e20`.
- PR contains 7 commits and 22 changed files; no PR conversation comments returned.
- Inspected README and all Markdown documents, dependencies, Dockerfile, API security/storage logic, vision pipeline and dashboard labels. No AGENTS.md found in the checkout.

## Findings and exact editorial response

| Priority | Finding | Proposed correction / required evidence |
| --- | --- | --- |
| Blocking | Demo GET returned 502 from this environment | Record availability failure without guessing cause; verify authentication and actual inference before final handoff |
| Blocking | Final AWS/Tailscale topology cannot be proven from current source or hostname | Document requested design separately from verified deployment; obtain sanitized task/sidecar config, source/image identity and AWS-origin evidence |
| Blocking | Data/model provenance has unresolved items, including 21 manually collected negative images | Retain audit and unresolved status; do not publish weights or unauthorized media |
| Blocking | Video URL, screenshots and authenticated event-specific fields are missing | Provide recording script and capture checklist; leave factual completion gates open |
| High | README and architecture omit Vercel/Funnel and emphasize optional S3 | Add final access design; describe S3 as disabled in authenticated mode and historical/optional otherwise |
| High | Landing Explore the system links to demo but copy says Interactive demo not yet online | Prepare replacement wording, conditional on observed availability; no Vercel deploy performed |
| High | Devpost links point at main while safeguards are on draft PR #4 | Link reviewed source and require approved immutable document links after owner-authorized publication |
| High | No hard stop for native decoding/inference | Preserve as technical limitation; do not equate upload/HTTP/cooperative timeout with cancellation |
| Medium | Old video script omits specificity and landing/authentication journey | Add full user journey, 50% specificity, failure case, team introduction and architecture |
| Medium | Dependency reproducibility overstated | State direct pins accurately; disclose moving base, apt, transitive dependencies and unpinned Chart.js |
| Medium | Old status appendices can be mistaken for current facts | Add historical labels; preserve prior test evidence rather than rewriting it as newly performed |
| Medium | Technical report diagram sampled after segmentation | Correct processing order: decode/sample first, then model and temporal analysis |

## Proposed file changes

Update README, Devpost candidate, architecture, technical report, video script, final checklist and access plan. Add official requirements review, screenshot checklist and this audit. Add historical notices to two older appendices. Runtime files, dependency versions, model identity and the frozen holdout report remain unchanged.

## Landing-page wording proposal (not deployed)

Current paragraph says access is being prepared while the CTA already links to the assigned demo.

While availability is unverified, use: **“Reviewer demo — availability pending verification”** and **“Explore the system opens the assigned HTTPS demo. Access requires privately supplied reviewer credentials. If unavailable, the project report and evaluation remain accessible below.”**

Only after the deployed route is verified, use: **“Authenticated reviewer demo”** and **“Explore the system opens the FloodLens dashboard over HTTPS. Reviewer credentials are supplied privately. The demonstration analyzes uploaded images and prerecorded videos.”**

After document approval, point report/architecture links at the approved immutable commit, not old main files. Landing-page source is not present in this repository; this task does not modify its separate deployment.

## Claims retained and constrained

Official YOLO11n-seg MultiDomain; confidence 0.25; imgsz 960; approximately one sample/second; 5-sample sliding window with at least 3 positives. Frozen evaluation: TP 10 / TN 5 / FP 5 / FN 0; Accuracy 75%, Precision 66.67%, Recall 100%, Specificity 50%, F1 80%.

Metrics are video-level results on twenty videos, not pixel-level segmentation quality, calibrated risk or general performance guarantees. Preview is one representative frame. No live-camera or operational emergency claim. Historical October 13 AWS+S3 validation is distinct from authenticated PR #4 and final Funnel placement.

## Security and validation scope

The initial 66 tracked files were searched for AWS access-key formats, GitHub tokens, Tailscale credentials, private-key headers and credentials embedded in URLs; none matched. Manual review of authentication examples found placeholders/test fixtures, not verified live credentials. This is a bounded source scan, not a complete Git-history, deployment-secret or vulnerability audit. Neither actual demo login value is included in the proposal.

Public URL audit: 26 distinct URLs checked; 21 returned 200, 4 returned 403, and 1 returned 502. No 404 was observed. Official competition content was available through the web-research tool despite 403 responses in the direct HTTP checker. The unrelated Figshare link remains access-unverified. All three documents linked from the live landing page returned 200, but point at older main-branch content. Original local Markdown file links resolved. Public-link results are recorded separately in the review package: a 502, timeout or automation/access restriction is not automatically proof of a permanently broken URL. The landing CTA target was inspected directly in retrieved HTML. Live authenticated UI behavior was not tested.

No application tests were rerun for this documentation-only proposal. Existing 21-test results are historical and use stubbed inference; they are not claimed as new validation. Final checks passed for whitespace, local file links, unchanged protected files, core metric/architecture consistency and standard credential patterns. The Devpost tagline has 121 characters. Patch applicability is checked against the reviewed baseline in the review package.

## Remaining owner decisions

Approve documentation before GitHub publication; resolve current demo access and AWS origin; complete rights evidence; record permitted media; inspect actual Devpost fields and private-access mechanism. Publishing these documents does not authorize deployment, merge or final submission.
