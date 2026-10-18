# FloodLens AI — Final Submission Checklist

Review date: 2026-10-18. Editorial preparation is complete as a proposal; the project is not yet certified ready for submission. No final submission has been made.

## Prepared in this proposal

- [x] Inspect PR #4, open/draft at 24ea9a8, and its 22-file change set against main.
- [x] Revise README, Devpost copy, architecture, technical report, access notes and recording script.
- [x] Preserve YOLO11n-seg MultiDomain, confidence 0.25, imgsz 960, five samples and three positives.
- [x] Preserve frozen 20-video TP 10 / TN 5 / FP 5 / FN 0; Accuracy 75%, Precision 66.67%, Recall 100%, Specificity 50%, F1 80%.
- [x] Prepare the screenshot plan and public-source competition requirements review.
- [x] Distinguish historical AWS/S3 evidence from authenticated, S3-disabled judge-mode behavior.
- [x] Keep runtime, checkpoint and holdout unchanged; no training or inference run.

## Owner review and publication

- [ ] Approve the documentation diff before a GitHub commit/push. Do not merge PR #4.
- [ ] Publish approved documents on the review branch; use immutable links to that approved commit in final submission material.
- [ ] Update the landing-page availability copy and document links after owner approval; do not promise uptime until verified.
- [ ] Decide whether the displayed architecture is actually deployed on AWS; record evidence rather than assuming from the hostname.

## Access and technical evidence

- [ ] Resolve the demo's observed 502 and verify external authentication plus real image/video analysis with authorized development media.
- [ ] Record the exact deployed source commit, image digest, checkpoint identity and sanitized task/sidecar configuration.
- [ ] Document stable Tailscale identity across task replacement, private secret injection, network restrictions and HTTPS proxy trust.
- [ ] Explicitly address the unresolved hard native-inference/decoding deadline; do not claim the cooperative timer cancels stuck work.
- [ ] Complete production dependency/image locking or clearly document the residual reproducibility limit. Pin the Chart.js CDN through a separately approved code change if selected.
- [ ] Verify desktop/mobile display and private/session storage behavior on the final deployed version. Historical local tests need not be repeated without a specific deployment difference.
- [ ] Agree the judging access period, cost authorization and shutdown plan separately; do not start resources in this review.

## Rights and media

- [ ] Resolve documented data/model-use questions; the 21 manually collected negative images still lack complete provenance in the current audit.
- [ ] Choose owned/licensed demonstration media and record permissions and attribution for every published frame.
- [ ] Record and review the actual video using video_script_en.md; no checkpoint or training-media upload.
- [ ] Capture the approved screenshot set; no credentials in either login field or any surrounding UI.
- [ ] Upload the video only with authorization; verify judge-accessible playback and actual duration.

## Devpost handoff

- [ ] Inspect the authenticated event-specific form, including mandatory extra questions, attachment settings and private-field visibility.
- [ ] Fill actual team identity and provide report, architecture, source, demo and final video links.
- [ ] Supply credentials only through a verified private judge channel.
- [ ] Resolve the official deadline discrepancy; plan against the earlier schedule time in competition_requirements_2026-10-18.md.
- [ ] Preview the final project page for factual consistency, readable media and functioning links.
- [ ] Owner authorizes and performs final submission separately. Do not submit as part of this task.

## After judging — separate authorization

- [ ] Stop the approved runtime and verify tasks/autoscaling state.
- [ ] Revoke demo access/routing as agreed and review residual costs.
- [ ] Retain scientific evidence and licensed submission material; do not delete resources without approval.
