# FloodLens AI — Devpost Final Copy Candidate

Editorial revision: 2026-10-18. Prepared for owner approval; not submitted. Copy the public narrative sections below into Devpost. Publishing remains blocked by the release checklist, especially demo availability, actual AWS origin, video URL and rights review.

## Project name
FloodLens AI

## Tagline
Experimental flood segmentation in road images and recorded videos with OpenCV 5, YOLO11, temporal verification, and AWS.

## Inspiration
Flooded roads can disrupt mobility and put people at risk. Road imagery contains useful visual evidence, but reflections, rain and wet pavement make automated interpretation difficult. FloodLens AI explores how computer vision can help researchers inspect that evidence while making uncertainty visible.

## What it does
FloodLens AI analyzes uploaded road images and prerecorded videos. It predicts potential flood regions with the official YOLO11n-seg MultiDomain checkpoint and displays a cyan segmentation overlay, segmented image area and, for videos, a time-indexed analysis.

The video pipeline samples approximately one frame per second. A sliding window contains five samples and requires at least three positive predictions. A video is `CONFIRMED` when at least one complete window meets that rule, `NOT_CONFIRMED` when none does, or `INSUFFICIENT_DATA` when fewer than five usable samples are available. Single images produce visual candidates rather than temporal confirmation.

`CONFIRMED` describes an algorithmic result, not independent verification of floodwater. Segmented area is a proportion of image pixels, not water depth. Experimental risk labels are heuristics, not calibrated danger probabilities. This is a research prototype, not an operational emergency system or a live camera service.

## How we built it
OpenCV 5 performs substantive media processing: `cv2.imdecode` decodes images, `cv2.VideoCapture` samples recorded video, and `cv2.fillPoly` and `cv2.countNonZero` turn segmentation polygons into a union mask and image-area measurements. OpenCV also produces the visual overlay. YOLO11n-seg supplies the learned predictions at confidence **0.25** and **imgsz 960**.

The backend uses Python, FastAPI, PyTorch and Ultralytics in a Docker container. The interface shows the original media next to the predicted region. For video, the preview is one representative sampled frame with the largest predicted area, not a fully annotated video.

The judge-access architecture is **Vercel landing page → Tailscale Funnel HTTPS → AWS ECS/Fargate → FloodLens API**. Vercel provides navigation; uploads go to the demo origin. The final AWS design places Tailscale alongside the API. The authenticated review configuration disables S3 persistence and shared server history; browser-session metadata supports reviewing the current session. This design is documented separately from verified deployment evidence.

## Challenges we ran into
Wet pavement, reflections and nighttime lighting can produce persistent false positives. Temporal consistency can reject isolated predictions, but a visual mistake repeated across frames can still meet the confirmation rule. A separate hard-negative V3 experiment did not improve aggregate development classification results, so the original MultiDomain model remains official.

Reproducibility also requires more than source code: the checkpoint is held separately, training-data provenance has unresolved items, and demonstration availability must be verified independently of an attractive landing page.

## Accomplishments that we're proud of
We integrated media upload, segmentation, temporal analysis and visual explanations in one prototype. We documented an AWS ECS/Fargate functional smoke test on October 13, 2026, including optional S3 storage. That earlier storage-enabled test is distinct from the authenticated judge configuration. We also evaluated the frozen pipeline on an independent 20-video holdout and reported the errors rather than only successful examples.

## Evaluation and principal results
The frozen Final Holdout V2 contains 20 prerecorded videos: 10 flooded and 10 non-flooded. The confusion matrix is **TP 10, TN 5, FP 5, FN 0**.

| Video-level metric | Observed result |
| --- | ---: |
| Accuracy | 75.00% |
| Precision | 66.67% |
| Recall | 100.00% |
| Specificity | 50.00% |
| F1 score | 80.00% |

All ten flood videos were detected in this small sample, while five negative videos were incorrectly confirmed. These results do not establish universal recall, operational safety or pixel-level segmentation accuracy. Persistent false positives remain the main limitation. The holdout and official parameters remain frozen; this submission preparation does not rerun evaluation or train a model.

## What we learned
Model confidence and temporal persistence are not the same as correctness. Separating visual predictions, temporal decisions and experimental risk makes results easier to interpret. Honest failure analysis, privacy controls and clear deployment evidence matter as much as the interface.

## What's next
Future research will examine more diverse scenes in a new independent evaluation, improve discrimination of reflective roads, and investigate camera calibration and human review. Physical water-level sensors and weather-data fusion are future ideas, not implemented features. Model-use and media permissions must be resolved before broader distribution.

## Built with
OpenCV 5, Python, Ultralytics YOLO11n-seg, PyTorch, NumPy, FastAPI, Docker, Amazon ECR, AWS ECS/Fargate, Tailscale Funnel, Vercel, JavaScript, Chart.js. Amazon S3 was used in the historical optional-storage validation; it is disabled in the authenticated demo configuration.

## Public links
- Landing page: https://floodlens-ai-vert.vercel.app
- Judge demo: https://floodlens-judge.tail1bb8f1.ts.net/
- Source: https://github.com/joa0lucassi/floodlens-ai
- Reviewed source: https://github.com/joa0lucassi/floodlens-ai/tree/security/judge-demo-final-review-2026-10-15
- Historical evaluation: https://github.com/joa0lucassi/floodlens-ai/blob/security/judge-demo-final-review-2026-10-15/docs/final_holdout_v2_results.md

## Operator notes — do not paste into the public narrative
- This is a copy candidate, not a claim that the live demo is ready. On 2026-10-18, the landing returned 200 and the demo returned 502 from the review environment. Resolve and verify the AWS route before publishing the final architecture as deployed fact.
- Video URL: pending recording and owner-authorized hosting. Use the actual final URL, never a placeholder.
- Attach/link the approved technical report and architecture. This proposal is not on the remote branch yet; existing remote documents are older versions. After owner-approved commit, use immutable links to that new commit without merging PR #4.
- Verify the actual team identity, category and event-specific fields in the authenticated form. Overall awards fit the implementation; COOL and Agentic Vision eligibility is not claimed.
- Provide demo credentials only through a confirmed private judge channel. Do not place either login value in public text, URLs, screenshots, source or video.
- The checkpoint is not public. Judge execution can be offered through the controlled demo; that does not resolve underlying data/model permission questions or make a source-only clone executable.
- See [release checklist](submission_final_checklist.md), [technical report](competition_technical_report_draft.md), [architecture](submission_architecture.md), and [rights audit](data_provenance_and_model_release.md).
