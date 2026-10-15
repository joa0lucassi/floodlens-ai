# Submission release checklist

Target supplied by the project owner: **26 October 2026**. Confirm the exact competition deadline/timezone and required judging availability in the current official submission form before submitting. This checklist is not confirmation that the submission or live demonstration is complete.

## Completed engineering evidence

- [x] Review PR #2 and existing follow-up PR #3; changes remain on a separate branch.
- [x] Run 21 model-free regression tests, including actual synthetic image/video decoding and temporal processing.
- [x] Preserve official 960/0.25 inference and 3-of-5 temporal rule.
- [x] Preserve frozen TP 10 / TN 5 / FP 5 / FN 0; accuracy 75%, precision 66.67%, recall 100%, F1 80%.
- [x] Prepare English architecture, access/cost/shutdown plan, reproduction notes and video script.
- [x] Keep weights, secrets and evaluation media out of changes.

## Required before public demonstration

- [ ] Review the final commit and complete real-model Python 3.14 Docker smoke tests with owned/licensed development media. Record model hash, commit, memory, latency and observed results.
- [ ] Validate a hard deadline that stops stuck native decoding/inference, plus edge header/body limits; do not confuse HTTP timeout with process cancellation.
- [ ] Render the authenticated dashboard in desktop and mobile browsers; check original media, cyan prediction preview, timeline, charts, error messages and session history.
- [ ] Inspect actual AWS plan, credits, service/task/image, VPC/subnets/SG, ECR privacy, S3 policy and CloudWatch retention.
- [ ] Agree stable hostname, TLS route, private secret injection and judging access period.
- [ ] Obtain explicit owner approval for the concrete cost estimate and network/service changes. No Paid Plan upgrade.
- [ ] Deploy only the approved immutable image; independently test HTTPS/auth, limits, origin isolation and actual inference.
- [ ] Record daily credit/spend readings and exact shutdown date; keep a reserve. Alerts are not a hard spending cap.

## Submission package

- [ ] Replace draft access/video placeholders with verified links; credentials only in a private judge field.
- [ ] Confirm permitted use of every demo image/video; keep source, creator, license and attribution.
- [ ] Resolve model-use/distribution questions; do not publish `best.pt`.
- [ ] Record the actual implementation using `video_script_en.md`; include limitations and false positives.
- [ ] Describe CONFIRMED as the temporal algorithm's output, not physical flood verification or water depth.
- [ ] Ensure the report, Devpost text and architecture describe the deployed version; retain historical test dates.
- [ ] Confirm source visibility/license and any reproduction/model-access requirements in competition rules.
- [ ] Preview and submit the final Devpost form manually or with separate explicit authorization.

## After judging

- [ ] Stop the existing service after authorization; verify desired/running/pending all zero and no autoscaling restart.
- [ ] Disable demo routing and revoke demo credentials after approval.
- [ ] Review residual ECR/S3/log costs and final delayed billing. Delete resources only with separate authorization.
