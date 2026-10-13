# FloodLens AI — AWS end-to-end validation (2026-10-13)

## Scope

This document records a successful cloud engineering smoke test, not a new independent model evaluation or a production-readiness claim.

## Tested configuration

- Official model: MultiDomain YOLO11 segmentation (models/flood_segmentation/best.pt)
- Inference: full frame, 960 px, confidence threshold 0.25
- Video sampling: once per second
- Temporal confirmation: sliding window of 5 samples, at least 3 positives, at least one confirmed window per video
- FastAPI 0.7.0, Docker CPU image, Amazon ECR, ECS/Fargate, and S3

The hard-negative V3 model was not promoted. On a 20-image development regression set, MultiDomain and V3 both yielded TP 9, TN 6, FP 4, FN 1 at image size 960 and confidence 0.25.

## Local integration verification

The development flood video produced matching results in the local API and Docker:

| Field | Result |
|---|---|
| Temporal status | CONFIRMED |
| Flood detected | True |
| Samples | 7 |
| Raw positive samples | 7 |
| Confirmed windows | 3 |
| First confirmation | 4 seconds |
| Heuristic risk | MODERATE |

Additional negative development checks:

| Video | Expected | Result |
|---|---|---|
| rain_no_flood_001.mp4 | No flood | NOT_CONFIRMED, 1/21 positives, 0 confirmed |
| wet_reflective_001.mp4 | No flood | False positive, 16/20 positives, 12 confirmed |
| night_reflective_001.mp4 | No flood | False positive, 3/16 positives, 1 confirmed |

The temporal rule helps suppress isolated false detections, but persistent wet-pavement/reflection errors remain.

## Cloud deployment and functional test

1. Updated Docker image pushed to the existing floodlens-api Amazon ECR repository.
2. Existing ECS service deployed and stabilized at one running task using task definition floodlens-task:3 (1 vCPU, 2 GiB RAM, container port 8000).
3. Publicly reachable GET /health returned status=healthy, model_loaded=True, s3_enabled=True, version=0.7.0.
4. POST /analyze/video was tested using the development flood video.

| Field | AWS result |
|---|---|
| Temporal status | CONFIRMED |
| Flood detected | True |
| Samples | 7 |
| Confirmed windows | 3 |
| First confirmation | 4 seconds |
| Heuristic risk | MODERATE |
| Storage saved | True |

The observed chain was: video upload → ECS API → YOLO inference → temporal confirmation → heuristic risk → successful S3 save.

This is a successful functional smoke test, **not** evidence of production reliability, performance capacity, emergency alert safety, or water-depth measurement.

## Cleanup and costs

After testing, the ECS service was scaled to zero. A later ECS query confirmed:

    Desired = 0
    Running = 0
    Pending = 0

At that point, no ECS service tasks were running. Other AWS resources (such as S3 storage, ECR image storage and logs) can still incur charges. Account IDs, public IPs, network IDs and credentials are intentionally excluded.

## Evaluation integrity

The frozen Final Holdout V2 was not rerun for this integration. Its earlier independent results remain TP=10, TN=5, FP=5, FN=0 on 20 videos. See docs/final_holdout_v2_results.md.

## Next steps

- Update the README Development Status; it still describes the old 640px API without temporal confirmation.
- Document reproducible local and Docker commands.
- Prepare competition demonstration materials and clearly state known false-positive limitations.
