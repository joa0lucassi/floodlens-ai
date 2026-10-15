# FloodLens AI — Devpost Submission Draft

**Status:** editorial draft, 2026-10-15. Not submitted. Keep this document in English for the international judging panel. Replace every `[TO COMPLETE]` field with a real verified value before submission.

## Project name

**FloodLens AI**

## Tagline

**Visual flood detection for urban roads using OpenCV 5, YOLO segmentation, temporal verification, and AWS.**

## Short description

FloodLens AI analyzes uploaded road images and recorded video to flag potential urban flooding, visualize predicted flood regions, and evaluate whether detections persist over time. Built with OpenCV 5, YOLO11-seg, FastAPI, Docker, and AWS.

## Inspiration

Flooded streets disrupt traffic, damage property, and create dangerous situations. Cities often already have road cameras, but interpreting video footage manually does not scale easily. We wanted to explore whether computer vision could turn recorded street footage into useful, interpretable evidence for researchers and future monitoring teams.

FloodLens AI is a research prototype—not an emergency response system. The current implementation analyzes **uploaded images and prerecorded videos**, not live camera streams.

## What it does

- Accepts a road-scene image or recorded video through a web dashboard.
- Uses a fine-tuned YOLO11n segmentation model to identify **potential flood regions**.
- Uses OpenCV 5 to decode video, reconstruct segmentation masks, estimate visible image area, and generate a cyan overlay for inspection.
- For video, samples approximately one frame per second and applies a sliding window of five samples. **At least three positive samples** in a complete window are required for a temporal confirmation.
- Reports `CONFIRMED`, `NOT_CONFIRMED`, or `INSUFFICIENT_DATA` for video, together with an area timeline and an experimental heuristic risk category where applicable.
- Can save uploaded media and analysis JSON in Amazon S3 when cloud storage is configured; local mode works without S3.

The term **confirmed** refers to the algorithm's temporal rule; it does **not** mean physical verification that water is present or that a road is safe/unsafe.

## How we built it

**Computer vision:** OpenCV 5 (`cv2.VideoCapture`, `cv2.imdecode`, `cv2.fillPoly`, `cv2.countNonZero`, and visualization/image processing) with a YOLO11n-seg model trained on multiple road-flood image sources. Inference uses a confidence threshold of 0.25 and 960-pixel input size.

**Temporal decision layer:** The model processes approximately one frame per second. Consecutive five-sample windows are tested for three or more detections. Videos with fewer than five usable samples are reported as insufficient rather than assigned a definitive video label.

**Interpretable interface:** A responsive dashboard compares the uploaded frame/video with a cyan mask preview, displays area-versus-time information and status labels, and distinguishes visual candidates from temporally confirmed results. For video, the preview is one representative sampled frame with the largest predicted area; it is not a fully annotated video.

**Backend and deployment:** Python, FastAPI, Docker, PyTorch, and Ultralytics. An AWS container deployment was functionally validated using Amazon ECR, Amazon ECS/Fargate, and S3. The ECS service was scaled to zero tasks after validation to limit compute costs; **there is no claim that the cloud dashboard is continuously online**.

## Challenges we ran into

Wet asphalt, reflections, ordinary puddles, rainfall, and nighttime lights often look similar to real flooding. Early model predictions included false positives and incomplete segmentation masks. Adding hard-negative examples in a separate V3 experiment did not improve the aggregate development-set confusion matrix, so we retained the original MultiDomain checkpoint as the official model.

A temporal consistency rule helps reject isolated false detections but cannot correct persistent visual mistakes. We deliberately report these failures rather than hiding them.

## Accomplishments that we're proud of

- Built an end-to-end computer vision prototype with real frame processing and segmentation.
- Added explicit temporal decision logic and honest `INSUFFICIENT_DATA` handling.
- Created a usable web interface with visual segmentation explanations and time-series metrics.
- Verified an end-to-end AWS path: upload → inference → temporal decision → risk heuristic → S3 metadata/media save.
- Performed an independent, frozen video holdout evaluation and recorded the full confusion matrix.
- Reproduced the application from a fresh Git clone with Docker and a separately provided official model checkpoint.

## Experimental evaluation

**Frozen Final Holdout V2:** 20 real prerecorded videos: 10 with flooding and 10 without. The selected model and configuration were frozen before this evaluation.

| Outcome | Count |
| --- | ---: |
| True positives | 10 |
| True negatives | 5 |
| False positives | 5 |
| False negatives | 0 |

| Video-level metric | Observed result |
| --- | ---: |
| Accuracy | 75.00% |
| Precision | 66.67% |
| Recall | 100.00% |
| Specificity | 50.00% |
| F1 score | 80.00% |

**Important context:** This is a small 20-video research evaluation, not evidence of universal 100% recall or deployment-level safety. Five non-flood videos were falsely confirmed. We did not retune thresholds using the frozen evaluation set.

The reported segmented area is a **percentage of image pixels**, not a calibrated physical measure of water depth. The risk category is an experimental heuristic, not an official flood severity or probability estimate.

Detailed results: [Final Holdout V2](final_holdout_v2_results.md).

## AWS integration

An AWS end-to-end smoke test on **October 13, 2026** validated a CPU Docker workload distributed through ECR, running on ECS/Fargate, with optional results storage in S3. The deployed API responded to health checks, processed a development flood video, and reported successful S3 storage.

After this validation, the ECS service was intentionally scaled down to zero running tasks. The dashboard remains fully testable in local Docker mode without AWS credentials. This validated deployment is **not** evidence of long-term uptime, capacity planning, or a hardened public service.

Evidence: [AWS validation log](aws_end_to_end_validation_2026-10-13.md).

## Reproducibility

- **Source:** https://github.com/joa0lucassi/floodlens-ai
- **Pinned runtime:** `Dockerfile` and `requirements-prod.txt`
- **Independent installation check:** [clean-clone Docker smoke test](clean_clone_smoke_test.md) — passed locally with an authorized separately supplied checkpoint; `/health` and a real video analysis were successful.
- **Model file:** `models/flood_segmentation/best.pt`. The official checkpoint's SHA-256 is recorded in the repository's provenance audit and verified by `scripts/verify_official_model.py`.
- **Model availability for reviewers:** [TO COMPLETE — authorized judge-access mechanism]. GitHub does **not** currently contain the weights.

## Responsible use and limitations

FloodLens AI is intended for research and demonstration. It is not a live CCTV/RTSP monitor, an autonomous alarm system, a calibrated flood-depth estimator, or an emergency-response authority. Real camera deployments would require stronger validation, privacy and data retention policies, secured uploads, operational monitoring, and human review.

Training-data provenance is documented in [model and dataset provenance](data_provenance_and_model_release.md). Some manually collected hard-negative training images have unresolved source rights; model redistribution is pending review. No unlicensed training media should be included in the submission package. Competition material permissions must be checked separately.

## What we learned

Model confidence and visual consistency are not substitutes for real-world correctness. Separating image-level predictions, temporal confirmation, and heuristic severity makes the interface more scientifically honest. Building a reproducible deployment and explicitly documenting failure cases is essential when developing computer vision tools for safety-relevant contexts.

## What's next

- Evaluate more diverse flooding/non-flooding scenes, particularly heavy reflections and nighttime roads, in a **new independent** test set.
- Improve segmentation robustness without tuning against the frozen evaluation data.
- Study camera-specific calibration, privacy, and human-in-the-loop review.
- Explore future fusion with verified physical water-level sensors and weather data.
- Resolve third-party data rights and provide judge-accessible model execution and demonstration evidence.

## Built with

OpenCV 5, Python, Ultralytics YOLO11n-seg, PyTorch, FastAPI, NumPy, Docker, AWS ECS/Fargate, Amazon ECR, Amazon S3, JavaScript, Chart.js.

## Project links — complete before publishing

- Repository: https://github.com/joa0lucassi/floodlens-ai
- Technical report: https://github.com/joa0lucassi/floodlens-ai/blob/main/docs/competition_technical_report_draft.md
- Architecture: https://github.com/joa0lucassi/floodlens-ai/blob/main/docs/submission_architecture.md
- Demonstration video (public or unlisted, **maximum 5 minutes**): **[TO COMPLETE]**
- Working web endpoint **or arranged live screen-share**: **[TO COMPLETE]**
- Judge instructions for accessing authorized weights: **[TO COMPLETE]**
- Participant/team identity, if requested by Devpost: **[VERIFY IN ACCOUNT]**

## Competition alignment

Main competition **overall awards**, not the optional COOL/Agentic Vision categories. This project has not implemented the specified COOL-on-Graviton workload or a multi-step agent perception–decision–action workflow; do not claim either optional category.

Official competition reference: https://opencv26.devpost.com/
