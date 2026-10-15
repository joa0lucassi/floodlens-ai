# Judge access and deployment plan — 2026-10-15

## Actual status

Code review and local model-free tests are implemented in the review branch. No AWS resource was changed or started. The cloud browser returned `Site Unavailable` for the ECS console on the initial attempt and one reload. Consequently cluster, task revision, ECR digest, VPC routes, security groups, S3 policies, CloudWatch, balance, and account-plan eligibility remain **unverified in this session**. Existing resource names and the approximately USD 99.34 balance are owner-provided, not newly observed.

The Oct 13 AWS test and earlier developer-reported clean-clone test are historical evidence, not validation of this branch. No production checkpoint, authorized road-media development set, Docker engine, or live AWS credentials were available here. Do not mark public deployment complete.

## Cost and architecture decision

Reuse the existing ECS service, one Linux/x86 Fargate task, 1 vCPU / 2 GiB, existing ECR, existing public subnet and internet gateway if verified. No new cluster, NAT gateway, load balancer or paid-plan upgrade is authorized.

Candidate with the lowest additional infrastructure overhead: a **named outbound tunnel** in the same task, with a stable HTTPS hostname, a local reverse proxy, and the app listening only on loopback. This requires a suitable existing domain/provider account and confirmation of its free-plan terms. Neither has been established. Media and authentication traffic traverse that provider; disclose this before approval. Quick/random tunnels are unsuitable as the submitted stable judge URL. Do not purchase a domain or create an account without approval.

Alternative: direct TLS proxy plus an existing domain and automated DNS updates after Fargate address changes. This adds certificate-storage/renewal and DNS-update risks. An ALB is a fallback only after a concrete separately approved estimate; it is not required for a single controlled demonstration. A static website alone cannot run the existing Python/YOLO inference.

Based on official us-east-1 Linux/x86 example rates retrieved Oct 15:

| Item | Estimate |
|---|---:|
| Fargate CPU + 2 GiB | USD 0.04937/hour |
| One public IPv4 | USD 0.005/hour |
| Combined baseline | USD 0.05437/hour |
| 24 hours | USD 1.30 |
| 7 days | USD 9.13 |
| 14 days | USD 18.27 |
| 30 days | USD 39.15 |

These are **baseline estimates, not a total or spending cap**. Additional charges include ECR storage, CloudWatch ingestion/storage, Secrets Manager or parameter/KMS requests, outbound data, existing S3 objects, and transient overlapping tasks during deployment. A 2-GiB task may need more memory with 960px inference and sidecars: measure first; do not silently resize. The final judging window is unknown, so a total deployment estimate cannot yet be approved responsibly.

Official references:
- https://aws.amazon.com/fargate/pricing/
- https://aws.amazon.com/vpc/pricing/
- https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html
- https://developers.cloudflare.com/tunnel/
- https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/

The AWS Free account plan is documented as not charging until upgrade; it ends after six months or credit exhaustion. Verify the **actual account plan**, current credits and covered services before activation. Never upgrade, join AWS Organizations, or enable another action that automatically upgrades the account. Budget notifications do not impose a hard cap.

## Deployment gates and execution after explicit approval

1. Verify plan, credit expiry, balance, Bills and existing storage/log consumption. Set an approved end timestamp and reserve balance. Record a timestamped baseline privately.
2. Inspect the existing cluster/service and task revision, actual ECR digest, CPU architecture, execution/task roles, public subnet route to internet gateway, SG inbound/outbound rules, logging retention, S3 public access block/encryption/lifecycle. Do not reproduce private identifiers in public docs.
3. Obtain an authorized checkpoint privately; verify with `scripts/verify_official_model.py`. Build and test Docker locally, including memory and CPU with permitted development media; never use the final holdout.
4. Inject `FLOODLENS_DEMO_PASSWORD` through ECS `secrets.valueFrom` referencing Secrets Manager or SSM SecureString, not plaintext task environment. Grant only the execution role read access to that exact secret (and KMS key if required). No AWS keys in the container. Set `FLOODLENS_DEMO_REQUIRE_AUTH=1` and `FLOODLENS_DEMO_REQUIRE_HTTPS=1`.
5. Use one Uvicorn worker and one ECS task; no autoscaling. The process-local limits are not a distributed rate limiter. S3 is disabled by judge mode even if a bucket is inherited. Shared history and risk endpoints return 403; browser-session history remains available.
6. Configure a verified TLS edge and local proxy with bounded upload time, body size and response timeout. Trust forwarded scheme only from the loopback proxy, never `*`. A tunnel must enforce HTTPS at its edge before forwarding. No public inbound 8000. Approve every network change separately. Do not delete existing rules/resources without approval.
7. Set no access-body/authorization logging, private ECR, non-root app, bounded task memory and ephemeral storage, 7-day operational-log retention if approved. Scrub proxy query strings and credentials. No request media in logs.
8. Register a new task revision; preserve revision 3 and previous image digest for rollback. Update the existing service only after the agreed cost approval. Record exact image digest and commit privately.
9. External validation: HTTPS valid certificate; HTTP cannot reach upload; unauthenticated dashboard/API/history denied; authorized PNG and 5–10s development MP4 produce actual inference and cyan preview; temporal timeline works; invalid/oversized media rejected; parallel uploads rejected; no S3 writes; direct origin port blocked. Check from a second network and record date/browser/results. Do not claim this from local TestClient tests.
10. Deliver HTTPS URL and credentials via the competition's private judge-access field, separately from public project text. Never commit credentials. Record start/end and observed spend daily.

## Residual engineering gates

The 180-second video budget is checked **between** sampled frames; it cannot interrupt a blocked native decoder or a single long model call. Proxy timeouts do not kill inference. Before wider exposure, implement and validate a supervised worker process with a hard deadline (or restrict to vetted judge media and explicitly accept this residual risk). Slow uploads also require a proxy total-time limit; Uvicorn keep-alive timeout is not an upload deadline. Global rate limiting can deny legitimate users during an attack. No penetration test or browser-rendered UI test was completed.

## Shutdown and rollback

After owner authorization, set desired count to zero on the existing service:

```sh
aws ecs update-service --region us-east-1 --cluster floodlens-cluster --service floodlens-task-service-fw9vt8sp --desired-count 0
aws ecs describe-services --region us-east-1 --cluster floodlens-cluster --services floodlens-task-service-fw9vt8sp --query 'services[0].{desired:desiredCount,running:runningCount,pending:pendingCount}'
```

Verify all three counts are zero and the demo URL no longer serves inference. Scaling to zero alone is not guaranteed if autoscaling remains configured; inspect it first. Revoke demo/tunnel credentials and disable the route after approval. Keep ECR, S3 and logs unless deletion is separately authorized; those resources can still consume credits. Record final Billing figures after billing-data delay. Rollback to the prior task definition does not authorize making its unprotected API public.

If account/network access or stable HTTPS prerequisites cannot be resolved: retain service at zero and prepare a permitted recorded walkthrough plus source and report. This has no hosting spend but is **not equivalent to an interactive demo**; confirm competition acceptance before relying on it.
