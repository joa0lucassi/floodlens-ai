# FloodLens AI — Technical Report (Submission Draft)

**Project:** FloodLens AI — Experimental Visual Monitoring of Urban Flooding  
**Competition:** OpenCV AI Competition 2026, powered by AWS  
**Author:** Joao Lucas, Computer Science, Federal University of Cariri (UFCA)  
**Status:** Draft prepared for final submission. Technical and legal checks listed at the end must be completed before submission.  
**Repository:** https://github.com/joa0lucassi/floodlens-ai

## 1. Abstract

FloodLens AI is a research prototype for identifying visually flooded regions in urban road scenes using real-world images and videos. It combines OpenCV 5 for frame acquisition and image-mask processing, YOLO11 instance segmentation, a temporal confirmation mechanism, an experimental heuristic risk score, and a FastAPI interface. The prototype is packaged with Docker and has been demonstrated on AWS ECS with analysis storage in S3.

On a frozen, independent 20-video evaluation set (10 flooded and 10 non-flooded videos), the evaluated pipeline identified all 10 flooded videos but also produced 5 false alerts in the negative group. Its video-level recall was 100%, precision 66.67%, specificity 50%, and F1 score 80%. These exploratory results show high sensitivity on that small sample and a clear remaining limitation: wet roads, rain and nighttime reflections can resemble actual flooding.

This system is **not an operational emergency alert service**. It does not measure physical water depth or provide calibrated probabilities of danger.

## 2. Problem, Users, and Potential Impact

Urban flooding can obstruct transportation, damage property, and expose people to hazards. Manual monitoring of numerous roads and intersections is difficult, while cameras that already observe public roads can provide potentially useful visual evidence.

Potential future users include municipal monitoring teams, researchers, road operators and emergency-management analysts. In its current state FloodLens is a research and demonstration tool. Before field deployment it would need larger representative evaluations, camera-specific calibration, privacy review, operational alert validation and human oversight.

## 3. System Architecture

The figure below reflects the implementation and validated cloud components. Cloud history is optional; the dashboard also operates in local mode without AWS credentials.

~~~mermaid
flowchart TD
    A[Uploaded image or video] --> B[FastAPI upload endpoint]
    B --> C[OpenCV 5 image decoding or video capture]
    C --> D[YOLO11 segmentation at 960 px]
    D --> E[Visual flood mask and area estimate]
    E --> F{Video?}
    F -->|No| G[Single-image flood candidate]
    F -->|Yes| H[Sample 1 frame per second]
    H --> I[Sliding 5-sample window]
    I --> J[At least 3 positives in a complete window]
    J --> K[Confirmed / not confirmed / insufficient data]
    K --> L[Experimental risk heuristic and temporal timeline]
    G --> M[FastAPI JSON response]
    L --> M
    M --> N[Browser dashboard]
    M --> O{S3 enabled?}
    O -->|Yes| P[Store uploaded media and analysis JSON in Amazon S3]
    O -->|No| Q[Browser-session display only]
    R[Docker image] --> S[Amazon ECR]
    S --> T[Amazon ECS / Fargate]
    T --> B
~~~

**Implementation reference:** `src/api/main.py`, `src/vision/inference.py`, `src/vision/video_inference.py`, `src/risk/risk_engine.py`, `src/storage/s3_storage.py`, `src/web/index.html`.

## 4. Substantive OpenCV 5 Usage

The project uses OpenCV in the computer vision pipeline, including:
- `cv2.VideoCapture` to decode video and select frames from temporal positions;
- `cv2.imdecode` to decode uploaded still images;
- `cv2.fillPoly` and `cv2.countNonZero` to rasterize segmentation polygons and calculate their visual area in the image.

OpenCV works with YOLO segmentation predictions; it is not claimed that OpenCV itself is the learned segmentation model.

## 5. Model and Temporal Method

- **Official selected model:** YOLO11n-seg MultiDomain checkpoint. The experimental V3 hard-negative checkpoint was not promoted.
- **Inference confidence:** 0.25.
- **Inference size:** 960 px.
- **Video sampling:** approximately one frame per second.
- **Temporal confirmation:** sliding window of five sampled frames, requiring at least three frames with a model flood detection; a video is considered confirmed if at least one complete window satisfies this rule.
- **Insufficient data:** videos without five usable samples do not receive a definitive video-level classification.

**Visual flooded area** is the percentage of pixels in the image covered by the union of segmentation masks. It is sensitive to camera viewpoint and framing and **must not be interpreted as water depth in centimeters**.

The **risk engine** heuristically combines average visual segmented area, area trend and model confidence. Its labels (LOW, MODERATE, HIGH, CRITICAL) are not validated emergency severity or calibrated probabilities. Risk assessment is suppressed when the temporal window does not confirm flooding.

## 6. Experimental Data and Model Development

The research used real-image sources such as RuaLivreIA and UFES-derived segmentation samples (Deepflood, Sazara, WebCOOS) in training or validation, with separate development and frozen final evaluation materials. Attribution and the full applicable terms for each third-party resource must be checked in the final data statement.

The V3 research stage assembled 108 visually reviewed hard-negative BDD100K images: rainy-day (40), nighttime (28), and rainy-night (40). The set contained 108 images paired with empty YOLO annotation files, representing scenes annotated as not flooded. This was a training experiment; it is **not** the independent evaluation set.

On the 20-image development regression set at 960 px and confidence 0.25, MultiDomain and the V3 model both achieved:

| TP | TN | FP | FN | Accuracy | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 9 | 6 | 4 | 1 | 75.00% | 69.23% | 90.00% | 78.26% |

The V3 model corrected one false positive and introduced another; therefore, it showed no net classification benefit and was not selected. **Do not infer improved robustness from adding negatives alone.** Before distributing or using V3-derived weights in competition materials, review dataset licensing and submission rights; the official deployed model is MultiDomain, not V3.

## 7. Independent Final Holdout V2

The independent video evaluation was prepared and the evaluation configuration was frozen before its one-time run.

- 20 real videos: 10 flooded, 10 negative;
- 960 px full-frame inference; confidence 0.25;
- one sample per second;
- 5-sample sliding window, 3 required positives;
- a video positive when at least one window is confirmed.

| Metric | Result |
|---|---:|
| True positives | 10 |
| True negatives | 5 |
| False positives | 5 |
| False negatives | 0 |
| Accuracy | 75.00% |
| Precision | 66.67% |
| Recall | 100.00% |
| Specificity | 50.00% |
| F1-score | 80.00% |

This evaluation is small: a recall value of 100% here does not prove universal detection performance. Five negative videos were incorrectly confirmed as floods; difficult conditions included reflective pavement, rain without actual flooding, and nighttime lighting. Temporal filtering reduces isolated false detections but not persistent semantic misclassification.

The frozen holdout was not used for post-evaluation threshold selection, and it was not rerun during the subsequent API integration. Further details: `docs/final_holdout_v2_results.md`.

## 8. Implementation and AWS Delivery

The application exposes:
- `GET /` — browser dashboard;
- `GET /health` — health and S3 availability;
- `GET /risk/latest` — locally generated, separate risk-assessment artifact (not automatically updated by each upload);
- `GET /analyses/history` — S3-backed history, available only when enabled;
- `POST /analyze/image` and `POST /analyze/video` — analysis endpoints.

The deployment was validated using a Docker image with CPU-based inference, Amazon ECR for image distribution, ECS/Fargate for running the service, and S3 for optional media and analysis JSON storage.

On 2026-10-13, the AWS deployment reached an ECS stable state, returned a healthy `/health` response with the model loaded and S3 enabled, then processed a development flood video. The AWS response included 7 samples, 3 confirmed windows, first temporal confirmation at 4 seconds, risk MODERATE, and `storage.saved=true`. The task service was subsequently scaled down and observed at Desired=0, Running=0, Pending=0.

This is an end-to-end **functional smoke test**, not evidence of production uptime, latency guarantees, scale or safety. The AWS service is intentionally not left running between tests to limit compute charges.

See `docs/aws_end_to_end_validation_2026-10-13.md` for the verified cloud test details.

## 9. Reproducibility

**Requirements:** Python compatible with the pinned runtime, OpenCV 5, Ultralytics, PyTorch CPU, FastAPI and Docker. The exact production dependencies are pinned in `requirements-prod.txt` and the CPU PyTorch installation is pinned in `Dockerfile`.

The trained model weight file is not versioned on GitHub. To reproduce inference, an authorized copy of the official MultiDomain checkpoint must be placed at:

    models/flood_segmentation/best.pt

From the repository root, with dependencies installed:

    python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000

Local health check:

    curl http://127.0.0.1:8000/health

Example video test (development video not included in the repository):

    curl -F "file=@data/flood_sample.mp4;type=video/mp4" http://127.0.0.1:8000/analyze/video

Docker:

    docker build -t floodlens-api:final .
    docker run --rm -p 127.0.0.1:8001:8000 floodlens-api:final

Judge-accessible availability of both code **and required model weights** must be arranged; this public repository alone is not a complete executable artifact without the checkpoint.

## 10. Responsible Use and Security Limitations

- False positives are significant, especially under glare, wet roads and nighttime reflections.
- The sample of independent videos is too small to generalize performance to all cities or cameras.
- Flooded image area is not physical depth. The risk label is an uncalibrated heuristic.
- Camera streams can contain identifiable people, vehicles or license plates; rights, minimization, privacy and retention policies are required for real operation.
- The current prototype should not be publicly exposed as a general-purpose, unauthenticated media-upload service without authentication, file size limits, rate limiting and hardened operational controls.
- Published competition materials must not expose AWS credentials, account identifiers, public task IPs or sensitive S3 information.
- The official model weights and any submitted media must have their distribution rights and attribution checked.

## 11. Roadmap

A future version may improve difficult negative discrimination through larger diverse training material, model verification and new independent evaluation. Another proposed direction is **FloodLens Hybrid**, combining fixed-camera visual extent, calibrated physical water-level sensors, and weather signals. These capabilities are proposals, **not** features claimed to be implemented.

## 12. Competition Submission Checklist — Open Items

- [ ] Validate third-party dataset, model, code and video rights and required attribution.
- [ ] Arrange authorized judge access to the required official model checkpoint.
- [ ] Deliver a judge-accessible live endpoint **or** coordinate a live screen-share demonstration. ECS is currently shut down when not in use.
- [ ] Produce a public/unlisted judge-accessible demonstration video (maximum 5 minutes) with team identification, working system, architecture, real results, and limitations.
- [ ] Export and review final report and architecture graphic for readability.
- [ ] Confirm the exact Devpost submission deadline and submit early.
- [ ] Check the final Kimi/dashboard implementation with the real API before describing it as completed.

## Sources in this repository

- `README.md`
- `docs/final_holdout_v2_results.md`
- `docs/aws_end_to_end_validation_2026-10-13.md`
- `src/evaluation/final_holdout_v2_evaluator.py`
- `src/evaluation/compare_multidomain_v3.py`

**Competition requirements:** https://opencv26.devpost.com/ (consult the current official rules and submission form).
