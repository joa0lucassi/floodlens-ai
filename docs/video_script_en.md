# FloodLens AI — Demonstration Video Script

Target: 4 minutes 40 seconds, including opening and closing. Recording plan only; no video has been created or uploaded by this review. Use the actual reviewed application and owner-authorized development media. Do not run the frozen holdout again.

## Shot list and narration

| Time | Screen/action | English narration |
| --- | --- | --- |
| 0:00–0:20 | Show the presenter and title; identify Joao Lucas and UFCA. | “I'm Joao Lucas, a Computer Science student at the Federal University of Cariri. FloodLens AI is a research prototype that identifies potential urban flooding in uploaded road images and prerecorded videos.” |
| 0:20–0:40 | Open the Vercel landing page and click **Explore the system**. | “This landing page introduces the project. Explore the system opens the HTTPS demonstration, where reviewers can inspect actual model results.” |
| 0:40–0:50 | Show an empty authentication prompt only, then cut to the authenticated dashboard. Never show either login value, autofill or credential entry. | “Access is restricted to reviewers. Credentials are supplied privately.” |
| 0:50–1:15 | Select an authorized road image; click **Analyze footage**; show original and cyan overlay. | “OpenCV decodes the image and processes YOLO11 segmentation masks. Cyan marks a predicted region. The reported percentage is image area, not water depth, and a single image is only a visual candidate.” |
| 1:15–1:45 | Upload an authorized 8–15 second development video. Show submission, then actual completion. Label any editing of the waiting period. | “For recorded video, the system samples approximately one frame per second. Inference uses the official MultiDomain YOLO11n segmentation model with confidence 0.25 and input size 960.” |
| 1:45–2:05 | Show original playback, representative segmentation preview and **Match frame**. | “The preview shows one sampled frame with the largest predicted area. It is a visual explanation, not a fully segmented playback of every video frame.” |
| 2:05–2:35 | Show **Temporal intelligence**, **Current assessment**, sample count and confirmed windows. | “Each complete sliding window contains five samples. At least three positives are needed for confirmation. CONFIRMED means this algorithmic rule was met, not physical verification of flooding. Fewer than five usable samples means insufficient data.” |
| 2:35–3:00 | Show an authorized difficult negative and its real result, or a clearly labeled historical failure summary if suitable media rights are unavailable. | “Wet roads and reflections remain difficult. Repeated false predictions can also meet the temporal rule. Temporal consistency does not eliminate persistent visual mistakes.” |
| 3:00–3:30 | Show approved architecture diagram and deployed-version evidence without account details. Use this narration only after the AWS route is verified. | “Vercel hosts the landing page. Tailscale Funnel provides HTTPS to the API hosted on AWS ECS/Fargate. OpenCV performs decoding and mask processing; YOLO predicts regions. The authenticated demo disables S3 persistence and shared server history.” |
| 3:30–4:05 | Display a results card: 20 videos, TP 10, TN 5, FP 5, FN 0 and all five metrics. | “On the frozen independent holdout of twenty videos, accuracy was 75 percent, precision 66.67 percent, recall 100 percent, specificity 50 percent, and F1 80 percent. Five negative videos were incorrectly confirmed. These are small-sample research results, not general performance guarantees.” |
| 4:05–4:30 | Return to the actual dashboard result and limitations. | “The prototype analyzes recorded media. It does not predict weather, measure physical depth or make emergency decisions. Future work needs broader independent evaluation, stronger discrimination of reflections and human review.” |
| 4:30–4:40 | Closing card with landing page, public repository and presenter identity. | “FloodLens AI makes visual predictions and their limitations inspectable. Thank you for reviewing the project.” |

## Recording checklist

- [ ] Resolve demo availability and verify the actual AWS route before recording architecture claims.
- [ ] Record application commit, image digest and checkpoint hash privately; use the approved runtime.
- [ ] Use an image within 8 MiB / 16 million pixels and a video within 48 MiB / 60 seconds / 2,073,600 pixels per frame. Prefer a short development clip with at least five usable samples.
- [ ] Confirm rights for every visible frame, music track, logo and voice; retain attribution records.
- [ ] Clear notifications, saved credentials, personal filenames and unrelated browser tabs.
- [ ] Record real upload-to-result transitions. If processing waits are shortened, label “Processing time shortened”; do not imply real-time throughput or fabricate timing.
- [ ] Use legible capture (1080p recommended), clear audio and English captions. These are production recommendations, not asserted contest resolution requirements.
- [ ] If the difficult negative is falsely confirmed, show and explain it honestly. Do not rerun holdout media for recording.
- [ ] Keep final exported duration at or below five minutes, including title cards.
- [ ] After owner authorization, host publicly or unlisted and check judge playback without an account. No hosting/upload occurs in this task.

Landing: https://floodlens-ai-vert.vercel.app
Demo: https://floodlens-judge.tail1bb8f1.ts.net/
Source: https://github.com/joa0lucassi/floodlens-ai
