# FloodLens AI — Submission Architecture (October 2026)

This diagram describes the **implemented research prototype** and the AWS path that was **functionally tested on 2026-10-13**. The ECS service was intentionally scaled to **zero running tasks after validation**. Dashed lines indicate optional elements; no continuously running camera feed or automatic emergency alert is implemented.

```mermaid
flowchart TB
  subgraph browser["Browser · Judge / researcher"]
    User["Upload road photo or prerecorded video"]
    UI["FloodLens dashboard<br/>Input · cyan mask preview · timeline · verdict · history"]
  end

  subgraph runtime["FastAPI container · local Docker or ECS/Fargate"]
    API["FastAPI<br/>/analyze/image · /analyze/video · /health"]
    Split{"Image or video?"}
    Image["OpenCV 5<br/>cv2.imdecode: uploaded still"]
    Video["OpenCV 5<br/>cv2.VideoCapture: video at ~1 frame/second"]
    YOLO["YOLO11n-seg · official MultiDomain<br/>confidence 0.25 · imgsz 960"]
    MASK["OpenCV 5<br/>cv2.fillPoly · cv2.countNonZero<br/>union mask + segmented-image-area %"]
    Candidate["Single image<br/>visual flood candidate only"]
    Temporal["5-sample sliding windows<br/>≥3 positive samples"]
    Status["Video decision<br/>CONFIRMED · NOT_CONFIRMED · INSUFFICIENT_DATA"]
    Risk["Experimental heuristic risk<br/>only assessed with temporal confirmation"]
    Preview["Optional visual explanation<br/>one representative masked frame / image<br/>OpenCV cyan overlay"]
    Result["Analysis JSON<br/>status · metrics · timeline · optional preview"]
  end

  subgraph aws["AWS · deployment path validated Oct 13"]
    ECR["Amazon ECR<br/>container image"]
    ECS["Amazon ECS / Fargate<br/>CPU application container"]
    S3["Amazon S3<br/>optional uploaded media + analysis JSON"]
  end

  User --> UI
  UI -- "multipart upload" --> API
  API --> Split
  Split -- "Image" --> Image
  Split -- "Video" --> Video
  Image --> YOLO
  Video --> YOLO
  YOLO --> MASK
  MASK --> Candidate
  MASK --> Temporal
  Temporal --> Status
  Status --> Risk
  Candidate --> Result
  Status --> Result
  Risk --> Result
  MASK -. "on-demand visualization" .-> Preview
  Preview -. "client-only base64 image" .-> Result
  Result --> API
  API -- "JSON response" --> UI
  API -. "when configured" .-> S3
  S3 -. "stored history" .-> API
  ECR -. "image for deployment" .-> ECS
  ECS -. "hosts identical FastAPI container" .-> API

  classDef cv fill:#133953,stroke:#54bce8,color:#e4f5ff
  classDef model fill:#1c3654,stroke:#7d8fff,color:#e4f5ff
  classDef cloud fill:#3b2c1a,stroke:#dca465,color:#fff1cf
  classDef note fill:#113a35,stroke:#62c6ad,color:#e6fff5
  class Image,Video,MASK,Preview cv
  class YOLO model
  class ECR,ECS,S3 cloud
  class Temporal,Status,Risk note
```

## What the diagram must not imply

- **Not continuous CCTV:** input is user-uploaded prerecorded media.
- **Not a depth sensor:** segmented-area percentage is camera-view dependent, not centimeters of water.
- **Not verified disaster response:** video `CONFIRMED` means the temporal rule was satisfied, not independent verification.
- **Not a continually available AWS website:** the deployment test was successful, but ECS was scaled to zero after testing.
- **Not a fully annotated video:** the returned visualization is one representative masked video frame (or still-image overlay), generated on demand.
- **Not stored previews:** base64 preview data is intentionally excluded from S3 result metadata.
- **No COOL / autonomous agent:** this is a standard OpenCV 5 + YOLO computer-vision pipeline, not the optional special-prize implementation.

## Evidence and implementation map

| Component | Implementation or evidence |
| --- | --- |
| Upload endpoints | `src/api/main.py` |
| Image decoding / mask / visualization | `src/vision/inference.py` |
| Video decoding, temporal windows, frame sampling | `src/vision/video_inference.py` |
| Risk computation | `src/risk/risk_engine.py` |
| S3 results storage | `src/storage/s3_storage.py` |
| Interactive web dashboard | `src/web/index.html` |
| AWS validation | `docs/aws_end_to_end_validation_2026-10-13.md` |
| Independent evaluation | `docs/final_holdout_v2_results.md` |
| Clean clone verification | `docs/clean_clone_smoke_test.md` |

**Submission note:** Embed this diagram in the technical report and, if the Devpost form expects an image upload, export the Mermaid to PNG or SVG without changing its meaning.


## Judge-demo review update — 2026-10-15

The separate security review branch adds guarded uploads, admission limits, HTTPS-required configuration, non-root container execution, and ephemeral judge sessions (S3 and shared history disabled). The official checkpoint, inference parameters and frozen evaluation remain unchanged. See [review evidence](judge_security_review_2026-10-15.md), [access/cost/shutdown plan](judge_access_plan.md), and [video script](video_script_en.md). Local model-free tests are not real-model or cloud validation. No HTTPS endpoint has been deployed during this review; earlier local/AWS passes do not validate the new branch. Weight distribution remains restricted pending rights review.
