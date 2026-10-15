# Demonstration video script — draft, target under five minutes

Use only footage owned by the team or individually licensed for this use. Do not show login secrets, AWS identifiers, task addresses, private ECR/S3 values, unapproved datasets or weights. Record the actual reviewed deployment after validation; do not substitute test stubs.

- 0:00–0:25: Introduce Joao Lucas, UFCA, and FloodLens AI: a research prototype for possible urban flooding in uploaded images and recorded videos.
- 0:25–1:15: Open the authenticated HTTPS dashboard (credentials off camera). Upload an authorized image. Compare original and cyan predicted region. Explain percentage is image area, not water depth.
- 1:15–2:15: Upload an authorized development video. Show original playback, the representative masked frame, timeline, and the three-of-five temporal rule. State that CONFIRMED is an algorithmic decision, not physical verification.
- 2:15–2:50: Show an authorized difficult negative example with its actual outcome. Do not cherry-pick or claim that temporal filtering eliminates persistent false positives.
- 2:50–3:35: Explain OpenCV decoding, polygon masks and overlays; YOLO11n-seg at 960 / 0.25; FastAPI; Docker; existing AWS ECS/ECR. Describe only HTTPS components actually deployed.
- 3:35–4:15: Show frozen results: TP 10, TN 5, FP 5, FN 0; accuracy 75%, precision 66.67%, recall 100%, F1 80%, on only 20 videos. No new holdout run.
- 4:15–4:45: Explain limitations, rights review, restricted demo access, ephemeral uploads and future work. Show public source URL and private-access instructions without secrets.

Before recording: freeze commit/image digest, check microphone and 1080p capture, prepare two permitted development files and source/license records, hide account information, confirm actual demo availability. Add English captions. Review the final rules/form for duration, hosting and access requirements before upload.
