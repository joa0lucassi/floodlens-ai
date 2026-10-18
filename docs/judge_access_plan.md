# Judge Access and Deployment Evidence

Updated proposal: 2026-10-18. This document plans access; it neither authorizes infrastructure changes nor establishes current AWS state.

## Public entry points

- Landing: https://floodlens-ai-vert.vercel.app
- Demo: https://floodlens-judge.tail1bb8f1.ts.net/
- Review candidate: https://github.com/joa0lucassi/floodlens-ai/pull/4

The intended final route is Vercel landing page → Tailscale Funnel HTTPS → AWS ECS/Fargate → FloodLens API. Vercel links the browser to the separate demo origin. Tailscale is intended to run beside the API in the same ECS task. No new ALB, NAT gateway, domain purchase or cluster is assumed by this design.

## Evidence register

| Date / source | Observed or reported | Limit |
| --- | --- | --- |
| 2026-10-13 repository AWS log | Earlier ECS/Fargate deployment processed a video with S3 enabled; later scaled to zero | Does not validate PR #4 or current Funnel routing |
| Earlier owner report in this conversation | Local Funnel, external HTTPS and authentication validated | Does not prove that the current hostname terminates at AWS |
| Earlier owner AWS inspection | Free Plan, credits and zero service tasks reported | Historical account information; not a current cost authorization |
| 2026-10-18 repository inspection | PR #4 open/draft at 24ea9a8; no checked-in task/sidecar deployment definition | Deployed source/image cannot be inferred from repository alone |
| 2026-10-18 unauthenticated public GET | Landing HTTP 200; Explore the system points to the demo; demo HTTP 502 from this environment | No authenticated access or inference validated; failure cause unknown |

## Verification needed before an availability claim

1. Record the actual task definition, application commit/image digest, Tailscale placement and the hostname's origin using read-only evidence. If it still forwards to a local machine, describe that accurately and keep AWS as a separately documented historical deployment until migration is verified.
2. Confirm that the deployed application has PR #4 safeguards, uses the frozen official checkpoint, trusts only the intended local proxy for HTTPS, and does not expose port 8000 generally.
3. Verify private authentication and an authorized image/video flow from an external network. No credentials belong in source, query strings, public text or recordings. `/health` alone is insufficient.
4. Verify the public endpoint after task replacement and explain identity/state handling. A hostname setting alone does not establish a persistent Tailscale identity.
5. Add a sanitized reproducible task/sidecar setup and secret-reference instructions after owner approval. Do not publish secret values or assume that credential-storage services have no cost.
6. Agree an access window and shutdown plan that supports judging. The service being scaled to zero and the endpoint being always available are incompatible claims.

## Privacy and resource limits in the reviewed source

Authenticated mode disables S3 and shared history/risk endpoints. Browser-session history is metadata. Image limits are 8 MiB and 16 million pixels; video limits are 48 MiB, 60 seconds and 2,073,600 pixels per frame. Upload reading has a total 60-second deadline. Video processing checks a 180-second cooperative budget between iterations; it cannot forcibly stop a stuck native decoder or model call. Do not market this as a hard execution limit or complete abuse protection.

## Costs and authorization

No current price estimate is asserted in this documentation pass. Before any activation, separately verify the account plan, credit eligibility/expiry, total service costs and owner-approved operating window. Consider compute, IPv4, transfer, logs, image storage, secret/state persistence and overlapping deployments. Zero running service tasks does not prove zero residual costs.

This task does not register a new revision, change desired count, create secrets/storage, deploy to Vercel or run inference. Any paid infrastructure action requires separate explicit authorization.
