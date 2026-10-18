# FloodLens AI — Final Submission Checklist

Review date: 2026-10-18. Documentation has been published to the review branch; the project is not yet finally submitted. The authenticated AWS/Tailscale judge route was validated end-to-end on 2026-10-17, then intentionally scaled to zero to stop continuous Fargate task usage.

## Completed

- [x] Inspect PR #4 and review its changes against `main`.
- [x] Revise README, Devpost copy, architecture, technical report, access notes and recording script.
- [x] Preserve YOLO11n-seg MultiDomain, confidence 0.25, imgsz 960, five samples and three positives.
- [x] Preserve frozen 20-video TP 10 / TN 5 / FP 5 / FN 0; Accuracy 75%, Precision 66.67%, Recall 100%, Specificity 50%, F1 80%.
- [x] Prepare the screenshot plan and public-source competition requirements review.
- [x] Preserve runtime code, checkpoint and holdout; no retraining or holdout rerun.
- [x] Validate local real-model Docker/browser flow for the reviewed runtime.
- [x] Validate AWS ECS/Fargate judge deployment with application + Tailscale sidecar.
- [x] Validate external HTTPS through Tailscale Funnel.
- [x] Validate Basic Auth from an incognito/external session.
- [x] Validate real model inference through the AWS-hosted judge route.
- [x] Inject judge and Tailscale credentials through AWS SSM SecureString references rather than source.
- [x] Remove public inbound TCP 8000 and confirm Funnel still works.
- [x] Set `FORWARDED_ALLOW_IPS=127.0.0.1` for the deployed API behind the local sidecar proxy.
- [x] Redeploy the Vercel landing page so **Explore the system** opens the final judge URL.
- [x] Scale ECS down after validation and confirm Desired=0, Running=0, Pending=0.

## Documentation / PR

- [x] Publish the reviewed documentation changes on the PR #4 branch.
- [x] Keep PR #4 open/draft; do not merge without separate owner authorization.
- [ ] Use immutable links to the final approved documentation commit in the Devpost handoff.
- [ ] Re-read the final PR diff after the deployment-evidence reconciliation commit.
- [ ] Decide whether the unresolved native hard-timeout limitation is accepted for submission or addressed before merge.

## Judge runtime — final activation check

- [ ] With owner authorization, set the ECS service to `Desired=1` for the judge window.
- [ ] Confirm Desired=1, Running=1, Pending=0.
- [ ] Confirm the running task uses `floodlens-task:5` (or an explicitly approved successor) and the intended pinned application image.
- [ ] Check the Tailscale machine identity/hostname after task recreation; correct any `floodlens-judge-1`-style collision before relying on the published URL.
- [ ] Open the Vercel landing page in an incognito/external session.
- [ ] Click **Explore the system** and confirm the final HTTPS URL opens.
- [ ] Confirm Basic Auth prompts and succeeds with privately supplied credentials.
- [ ] Run one authorized real image/video inference end-to-end.
- [ ] Confirm TCP 8000 remains unavailable as a general public entry point.
- [ ] Confirm `FORWARDED_ALLOW_IPS=127.0.0.1` and judge-mode S3/history restrictions remain intact.
- [ ] Keep the service running for the agreed judging period, then scale back to zero with separate authorization.

## Known technical limitations to disclose

- [x] Document that the video processing budget is cooperative and cannot forcibly terminate a stuck native OpenCV/model call.
- [x] Document that Tailscale node state is ephemeral across full ECS task replacement, so hostname identity must be checked on restart.
- [ ] Complete stronger dependency/image locking or retain the documented residual reproducibility limits.

## Rights and media

- [ ] Resolve documented data/model-use questions; the 21 manually collected negative images still lack complete provenance in the current audit.
- [ ] Choose owned/licensed demonstration media and record permissions and attribution for every published frame.
- [ ] Record and review the actual video using `video_script_en.md`; do not expose credentials or checkpoint files.
- [ ] Capture the approved screenshot set; no credentials in login fields or surrounding UI.
- [ ] Upload the video only with authorization; verify judge-accessible playback and actual duration.

## Devpost handoff

- [ ] Inspect the authenticated event-specific form, including mandatory extra questions, attachment settings and private-field visibility.
- [ ] Fill actual team identity and provide report, architecture, source, demo and final video links.
- [ ] Supply credentials only through a verified private judge channel.
- [ ] Plan against the earlier official schedule cutoff documented in `competition_requirements_2026-10-18.md` unless organizers clarify otherwise.
- [ ] Preview the final project page for factual consistency, readable media and functioning links.
- [ ] Owner authorizes and performs final submission separately.

## After judging — separate authorization

- [ ] Stop the approved runtime and verify Desired=0, Running=0, Pending=0.
- [ ] Revoke demo access/routing as agreed and review residual AWS costs.
- [ ] Retain scientific evidence and licensed submission material; do not delete resources without approval.
