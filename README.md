# FloodLens AI

> Computer vision system for experimental urban flood monitoring using OpenCV, YOLO segmentation, temporal analysis, FastAPI, Docker, and AWS.

## Overview

FloodLens AI is an experimental computer vision project designed to identify urban flooding from images and videos.

The project uses a YOLO11 segmentation model to detect visually flooded regions, OpenCV for video processing, temporal analysis to reduce isolated false detections, a heuristic risk engine, and a FastAPI backend that can be deployed using Docker and AWS infrastructure.

The project is currently under active development and is being evaluated for the OpenCV AI Competition 2026.

> **Important:** FloodLens AI is an experimental system and is not intended for operational emergency decision-making in its current stage.

---

## The Problem

Urban flooding can develop quickly and monitoring large urban areas manually is difficult.

Existing cameras can provide useful visual information, but automatically distinguishing real flooding from visually similar situations is challenging.

Examples include:

- wet pavement;
- reflections;
- heavy rain;
- nighttime lighting;
- vehicle headlights;
- shadows;
- shiny road surfaces.

FloodLens AI explores how computer vision can help automatically detect and monitor these situations.

---

## Research Pipeline

The latest evaluated video pipeline works as follows:

```text
VIDEO
  |
  v
Sample 1 full frame every second
  |
  v
YOLO11-seg
Inference size: 960
Confidence threshold: 0.25
  |
  v
Raw result for each sample
FLOOD or DRY
  |
  v
Temporal consistency
Sliding window of 5 samples
  |
  v
At least 3 of 5 are positive?
  |
  +---- YES ---> Flood confirmed
  |
  +---- NO ----> Not confirmed
```

The temporal window is sliding rather than divided into independent groups.

Example:

```text
0s  1s  2s  3s  4s
    1s  2s  3s  4s  5s
        2s  3s  4s  5s  6s
```

A video is classified as `FLOOD` if at least one temporal window confirms flooding.

---

## Why Temporal Analysis?

A segmentation model may occasionally produce an isolated false positive.

For example:

```text
DRY
DRY
FLOOD
DRY
DRY
```

Only 1 of the 5 samples is positive, so flooding is not confirmed.

However, temporal filtering cannot solve persistent semantic errors.

If wet pavement is incorrectly classified as flooding across several consecutive frames:

```text
FLOOD
FLOOD
FLOOD
FLOOD
FLOOD
```

the temporal system will also confirm flooding.

This is currently one of the main research challenges of FloodLens AI.

---

## Final Holdout V2

The latest independent evaluation used a frozen configuration before inference.

### Dataset

- 20 previously unseen real-world videos
- 10 flood videos
- 10 dry videos
- 1 frame sampled per second
- full-frame inference
- inference size: 960
- confidence threshold: 0.25
- temporal window: 5
- confirmation threshold: 3/5

No parameter tuning was performed after observing the holdout results.

### Results

| Metric | Result |
|---|---:|
| True Positives | 10 |
| True Negatives | 5 |
| False Positives | 5 |
| False Negatives | 0 |
| Accuracy | **75.00%** |
| Precision | **66.67%** |
| Recall | **100.00%** |
| Specificity | **50.00%** |
| F1-score | **80.00%** |

### Confusion Matrix

| | Predicted Flood | Predicted Dry |
|---|---:|---:|
| Actual Flood | 10 | 0 |
| Actual Dry | 5 | 5 |

All 10 flood videos were detected in this evaluation.

The primary limitation was false positives in difficult negative conditions, especially:

- wet and reflective pavement;
- rain without flooding;
- nighttime reflections;
- visually difficult road scenes.

Full evaluation details are available in:

```text
docs/final_holdout_v2_results.md
```

---

## Current Research Limitation

The main challenge is no longer simply isolated false detections.

The current model can produce **persistent semantic false positives**.

In some negative videos, wet or reflective pavement was classified as flooding across most of the analyzed frames.

This means that temporal consistency alone cannot solve the problem.

Future improvements should focus on making the vision model better distinguish:

```text
real urban flooding
        VS
wet / reflective road surfaces
```

---

## Flooded Area

FloodLens can estimate the percentage of the camera image occupied by regions segmented as flooding.

For example:

```text
Flooded area: 18.4%
```

This represents the **visual proportion of the image segmented as flood**.

It does **not** represent physical water depth.

Estimating water depth in centimeters would require additional calibration or physical sensing.

---

## Risk Engine

FloodLens includes an experimental heuristic risk engine.

It considers:

- average segmented flood area;
- temporal trend;
- model confidence.

The current levels are:

```text
LOW
MODERATE
HIGH
CRITICAL
```

These levels are experimental heuristics and are not calibrated emergency-risk probabilities.

They are intended for research and prototype development.

---

## System Architecture

```text
Camera / Video
      |
      v
OpenCV
      |
      v
YOLO11-seg
      |
      v
Flood segmentation
      |
      v
Temporal / Risk Analysis
      |
      v
FastAPI
      |
      +-------------------+
      |                   |
      v                   v
Dashboard              AWS S3
                          |
                          v
                  Analysis history

Containerization
      |
      v
Docker
      |
      v
AWS ECR
      |
      v
AWS ECS / Fargate
```

---

## Technology Stack

### Computer Vision

- OpenCV 5
- Ultralytics YOLO11-seg
- PyTorch
- NumPy

### Backend

- Python
- FastAPI
- Uvicorn

### Cloud

- AWS ECR
- AWS ECS / Fargate
- AWS S3

### Infrastructure

- Docker

---

## API

The current FastAPI application exposes the following endpoints:

```text
GET  /
GET  /health
GET  /risk/latest
GET  /analyses/history

POST /analyze/image
POST /analyze/video
```

Current API version:

```text
0.7.0
```

The root endpoint serves the FloodLens dashboard.

---

## Development Status

There are currently two related pipeline stages in the repository.

### API pipeline

The current API implementation uses the production `FloodAnalyzer` with:

```text
Inference size: 640
Confidence threshold: 0.25
```

### Research candidate

The independently evaluated Final Holdout V2 pipeline uses:

```text
Inference size: 960
Confidence threshold: 0.25
Sampling: 1 frame / second
Temporal window: 5
Confirmation: >= 3 positive samples
```

The `960 + temporal 3/5` candidate has been evaluated independently but has **not yet been integrated into the production API pipeline**.

This separation is intentional while experimentation continues.

---

## Project Structure

```text
floodlens-ai/
|
|-- docs/
|   `-- final_holdout_v2_results.md
|
|-- models/
|   `-- flood_segmentation/
|       `-- best.pt
|
|-- scripts/
|   `-- push_ecr.ps1
|
|-- src/
|   |
|   |-- api/
|   |   `-- main.py
|   |
|   |-- dataset/
|   |
|   |-- evaluation/
|   |   `-- final_holdout_v2_evaluator.py
|   |
|   |-- risk/
|   |   `-- risk_engine.py
|   |
|   |-- storage/
|   |   `-- s3_storage.py
|   |
|   |-- vision/
|   |   |-- inference.py
|   |   `-- video_inference.py
|   |
|   `-- web/
|       `-- index.html
|
|-- Dockerfile
|-- requirements.txt
`-- requirements-prod.txt
```

Large datasets, evaluation videos, model weights, and generated results are intentionally not versioned in the repository.

---

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/joa0lucassi/floodlens-ai.git
cd floodlens-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add the model

The trained model weights are not stored in GitHub.

The application expects the model at:

```text
models/flood_segmentation/best.pt
```

### 5. Start the API

```bash
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

The dashboard will be available locally on port:

```text
8000
```

---

## Docker

Build the image:

```bash
docker build -t floodlens-api .
```

Run locally:

```bash
docker run --rm -p 8000:8000 floodlens-api
```

---

## AWS Deployment

The project has been prepared for containerized cloud deployment.

```text
Docker image
     |
     v
AWS ECR
     |
     v
AWS ECS / Fargate
     |
     v
FloodLens API
     |
     +---- AWS S3
```

S3 integration stores uploaded media and analysis results when cloud storage is enabled.

---

## Evaluation Philosophy

The project separates development data from final evaluation data.

Final holdout sets are not intended to be reused for:

- threshold selection;
- parameter tuning;
- model selection;
- repeated experimentation.

This helps reduce evaluation leakage and provides a more realistic estimate of model behavior on unseen data.

---

## Roadmap

Current priorities include:

- reduce persistent false positives on wet pavement;
- improve robustness to reflections;
- improve nighttime performance;
- improve rain-without-flood discrimination;
- integrate the validated temporal pipeline into the API after further research;
- expand independent evaluation with more diverse environments;
- investigate camera-specific calibration.

### FloodLens Hybrid

A future research direction is combining computer vision with physical and meteorological sensing.

```text
Urban cameras
      +
Water-level sensors
      +
Weather data
      |
      v
Data fusion
      |
      v
FloodLens Hybrid
      |
      v
Urban flood monitoring
```

In this architecture:

- cameras provide visual extent and scene context;
- physical sensors provide calibrated water-level measurements;
- weather information can provide anticipation and operational context.

Low-power sensors could operate at reduced frequency during normal conditions and increase monitoring frequency during heavy-rain conditions.

---

## Scientific Considerations

FloodLens currently measures visual segmentation, not physical water depth.

Results depend on:

- camera position;
- perspective;
- environment;
- illumination;
- road surface;
- weather;
- training data distribution.

Therefore, a percentage of segmented image area should not be interpreted as a universal measurement of flood severity.

---

## Competition

FloodLens AI is being developed as a computer vision research project for the **OpenCV AI Competition 2026**.

The project focuses on practical use of computer vision for urban flood monitoring while documenting both successful results and current failure modes.

---

## Author

**Joao Lucas**

Computer Science student  
Federal University of Cariri — UFCA

GitHub: [joa0lucassi](https://github.com/joa0lucassi)

---

## Current Status

```text
Research prototype

Independent video evaluation completed
Recall:       100.00%
F1-score:      80.00%

Main open problem:
persistent false positives in difficult negative scenes
```
