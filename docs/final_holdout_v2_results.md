# Final Holdout V2 - Independent Video Evaluation

## Evaluation setup

The Final Holdout V2 was created as an independent video-level evaluation set.

- Total videos: 20
- Flood videos: 10
- Dry videos: 10
- Sampling rate: 1 frame per second
- YOLO inference size: 960
- Confidence threshold: 0.25
- Temporal window: 5 samples
- Temporal confirmation rule: at least 3 positive samples out of 5
- Video-level decision: FLOOD if at least one temporal confirmation occurs
- Full-frame inference
- No tiled inference
- No generic ROI filtering
- No color preprocessing

The configuration was frozen before running the final evaluation.

## Results

| Metric | Result |
|---|---:|
| True Positives | 10 |
| True Negatives | 5 |
| False Positives | 5 |
| False Negatives | 0 |
| Accuracy | 75.00% |
| Precision | 66.67% |
| Recall | 100.00% |
| Specificity | 50.00% |
| F1-score | 80.00% |

## Confusion matrix

| | Predicted Flood | Predicted Dry |
|---|---:|---:|
| Actual Flood | 10 | 0 |
| Actual Dry | 5 | 5 |

## Failure cases

| Video | Category | Raw positives | Confirmed samples | Max confidence |
|---|---|---:|---:|---:|
| dry_003.mp4 | wet_reflective | 19/20 | 16 | 0.89 |
| dry_004.mp4 | wet_reflective | 20/20 | 16 | 0.88 |
| dry_005.mp4 | rain_no_flood | 7/21 | 6 | 0.53 |
| dry_007.mp4 | night_reflective | 16/21 | 17 | 0.60 |
| dry_010.mp4 | difficult_negative | 12/12 | 8 | 0.77 |

## Interpretation

The system detected all flood videos in this evaluation, resulting in 100% recall.

However, 5 of the 10 negative videos were incorrectly classified as flood, resulting in 50% specificity.

The main remaining limitation is persistent semantic false positives. Wet pavement, reflections, rain, nighttime lighting, and other visually difficult conditions can be consistently interpreted by the segmentation model as flooding.

Temporal consistency can suppress isolated false detections, but it cannot correct a semantic error that persists across consecutive frames.

These results were recorded without modifying or retuning the pipeline after observing the holdout predictions.

## Important limitation

This evaluation contains only 20 videos. The metrics should therefore be interpreted as experimental results rather than evidence of production-level performance.

The holdout is frozen and must not be reused for parameter tuning.
