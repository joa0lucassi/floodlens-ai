# Security review and validation — 2026-10-15

Reviewed PR #2 at `c15ead522cdaa50c0d933ad4b48bb0abe8847d6f`, all five changed files and adjacent API/storage/dashboard/Docker paths.

## Findings and fixes

- Header-only upload rejection allowed chunked bodies to spool first: ASGI receive now counts actual bytes before multipart processing; 1 MiB multipart overhead plus route-specific cap. Endpoint file limits remain independent.
- Non-ASCII Basic credentials could raise TypeError in compare_digest: compare UTF-8 bytes. Malformed credentials remain rejected.
- Synchronous image decode/inference inside async route blocked the event loop: run as a synchronous FastAPI endpoint in its thread pool.
- Shared YOLO instance had no admission control: one analysis in flight per process, six analysis admissions/minute, sixty authenticated-area requests/minute including failed authentication. No unbounded rate-limit identity map.
- Added explicit HTTPS-required mode based on ASGI scheme; no manual trust of forwarded headers. Cross-origin browser POSTs denied.
- Image dimensions were checked after full decode: inspect Pillow headers before OpenCV allocation; reject empty/invalid images cleanly.
- Video duration relied on unchecked numeric metadata: reject nonfinite metadata, cap demo frames to 2,073,600 pixels, release capture on rejected metadata, check processing budget between frames.
- Untrusted filename suffix used for temporary file: choose suffix from accepted media type. Temporary video removed in finally.
- Shared S3 history, risk records and retention were inappropriate for shared judge credentials: judge-required mode forces S3 off and denies both shared-read endpoints.
- Storage exception details returned cloud internals: generic public messages. Default Docker access logs disabled; app now non-root with one worker and bounded server concurrency.
- Secret files excluded from Docker context. No model weights or media added.

## Executed checks

Python 3.12 host (production Docker targets Python 3.14), FastAPI 0.142.2, Starlette 1.8.0, OpenCV headless 5.0.0.93, NumPy 2.5.3, boto3 1.43.108, Pillow 12.3.0, httpx 0.28.1, python-multipart 0.0.32.

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
```

18 tests passed. Coverage: original four tests plus Unicode auth, HTTPS/forwarded-header rejection, chunked multipart cap, cross-origin upload rejection, rate limit, overlapping requests, dashboard HTML response, shared-history denial, empty image, image response/preview, pre-decode pixel cap, synthetic AVI temporal response and temp cleanup, invalid/overlong video metadata and unchanged official inference constants. Synthetic PNG/AVI are generated in tests; no external-media license or holdout use is involved. **YOLO inference is stubbed**; decoding, response handling, preview JPEG generation and temporal logic are real. This is not evidence of model accuracy or real segmentation.

`node --check` on extracted dashboard inline JavaScript: passed. `git diff --check`: passed. The dashboard layout was not browser-rendered in this environment. Docker build and Python 3.14 runtime not tested (Docker unavailable, private checkpoint absent). An httpx/Starlette deprecation warning does not fail tests.

No changes to `src/vision/inference.py`, risk engine, evaluation code or frozen holdout results. Official parameters remain 960 / 0.25 / 3 positives in a complete window of 5. No training, final evaluation or AWS operation was executed.

## Release disposition

Ready for code review; **not ready for merge/deployment as a fully validated live demo**. Complete real-model Docker/UI smoke tests, hard processing deadline/edge upload controls, private secret injection, AWS read-only inspection and approved cost/HTTPS design first. See [access plan](judge_access_plan.md). This is a targeted engineering review, not a comprehensive penetration test or dependency vulnerability audit.
