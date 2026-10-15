# Judge demo hardening — review before public access

This branch prepares the FloodLens API for a **temporary, access-controlled judge demonstration**. It does not configure AWS, HTTPS, load balancing, paid resources, or prove that the deployment is secure.

## Changes

- Optional HTTP Basic authentication guards the dashboard and API, including OpenAPI documentation. The `/health` endpoint stays readable for ECS checks. Local Docker behavior remains unchanged when no password is provided.
- With `FLOODLENS_DEMO_REQUIRE_AUTH=1`, startup fails closed if no password is configured.
- Strong demo password (at least 16 characters) required when enabled.
- API upload limits: images 8 MiB / videos 48 MiB; image resolution at most 16 million pixels. Header pre-check plus bounded file reads/copies.
- API video duration limit: 60 seconds, checked before model inference. This does **not** alter model predictions for accepted videos.
- No changes to YOLO checkpoint, threshold (0.25), image size (960), or 3-in-5 temporal decision.

## Local check (PowerShell)

```powershell
# Run in your own test environment, not in production
$env:FLOODLENS_DEMO_REQUIRE_AUTH = "1"
$env:FLOODLENS_DEMO_USERNAME = "judge"
$env:FLOODLENS_DEMO_PASSWORD = "YOUR_OWN_RANDOM_SECRET_AT_LEAST_16_CHARS"
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Visit `http://127.0.0.1:8000/` locally; the browser should request username and password. **Never send this Basic Auth credential over public HTTP**. For a remote demo, provide HTTPS termination at a trusted entry point.

Test the limited video and image upload routes and the health endpoint. Then repeat with the password unset (and the require flag unset) to confirm normal local behavior.

## AWS steps still required — not performed by these code changes

1. Review the ECS task definition and existing security group. Do **not** open TCP 8000 to the internet.
2. Provide `FLOODLENS_DEMO_PASSWORD` through AWS Secrets Manager or equivalent secret injection, not a source file or publicly visible task-definition value; set `FLOODLENS_DEMO_REQUIRE_AUTH=1`.
3. Configure a **stable HTTPS** entry point, TLS certificate, and allow only entry-point traffic to the container. Verify actual Free Plan credit eligibility and the running cost before enabling resources.
4. Configure trusted-edge **request-size/rate limiting**, concurrency/timeouts, and logging. The reviewed branch now counts streamed body bytes before multipart parsing. Edge total-upload deadlines and a supervised processing deadline remain deployment gates.
5. Prefer disabling S3 storage for the public demo unless there is a documented data-retention policy. If using S3, verify bucket permissions, encryption, lifecycle, and access controls.
6. Use only authorized demonstration media; check the data/model provenance audit before distributing weights or frames.
7. Test from an independent browser/network, monitor CloudWatch and Billing, and stop the ECS tasks afterward. Billing alerts are notifications, not a hard spending cap.

**Important:** Public GitHub alone is not runnable without an authorized model checkpoint. This change neither distributes weights nor establishes source-media rights. Do not deploy this branch to AWS or merge it into `main` before a local functional test and a separate security review.


See the subsequent [technical review](judge_security_review_2026-10-15.md) and [current deployment gates](judge_access_plan.md); this initial PR checklist alone is not a release approval.
