# Submission Screenshot Checklist

Capture plan, not a claim that screenshots exist. Suggested set: six primary images, plus two optional supporting captures. No exact count or resolution requirement was confirmed from the public competition requirements. Use 16:9, 1920×1080 as an editorial recommendation and inspect readability after upload.

| Done | Asset | Capture | Suggested English caption |
| --- | --- | --- | --- |
| [ ] | 01-landing.png | Actual Vercel hero with Explore the system and project identity; fix the stale access message first | FloodLens AI project overview and reviewer entry point. |
| [ ] | 02-image-segmentation.png | Authorized image next to actual cyan prediction, with area label and disclaimer visible | Predicted flood region; segmented image area is not water depth. |
| [ ] | 03-video-segmentation.png | Recorded video matched to its representative sampled overlay | Representative sampled frame from recorded-video analysis. |
| [ ] | 04-temporal-result.png | Timeline, actual verdict, samples, confirmed windows and first confirmation | Five-sample sliding windows require at least three positives. |
| [ ] | 05-architecture.png | Export the approved architecture diagram, after verifying AWS routing | Judge-access architecture with OpenCV 5 and AWS ECS/Fargate. |
| [ ] | 06-holdout-results.png | Clearly labeled results graphic, not a fake dashboard screenshot: TP 10 / TN 5 / FP 5 / FN 0 and all five metrics | Frozen 20-video holdout: 75% accuracy, 66.67% precision, 100% recall, 50% specificity and 80% F1. |
| [ ] | 07-failure-case.png | Optional authorized difficult negative with its real output; explain any false confirmation | Persistent reflections can satisfy the temporal rule incorrectly. |
| [ ] | 08-auth-empty.png | Optional empty authentication prompt, with no autofill or identifying login values | Restricted reviewer access over HTTPS. |

## Acceptance checks

- [ ] Every application result is real; the landing-page illustration is not presented as model output.
- [ ] Frame matches its displayed video timestamp and sample result; no invented or edited prediction regions.
- [ ] Neither login value appears in pixels, filenames, captions, metadata, address bars or browser suggestions.
- [ ] No AWS console screenshots, keys, account IDs, private storage paths, unrelated people or unreadable tiny text.
- [ ] Media permission, creator, source URL, license/consent and required attribution are recorded privately for each capture.
- [ ] Blur/redact personal information only where necessary and disclose redaction; do not alter scientific evidence.
- [ ] Label a generated results card or architecture graphic as such, not as a live application screenshot.
- [ ] Verify all captions against README, Devpost and the actual deployed interface.
