# Judge Access and Deployment Evidence

Updated: 2026-10-18. This document reconciles the repository review with the owner-observed deployment validation completed on 2026-10-17. It records evidence and remaining release checks; it does not authorize new paid infrastructure, publish secrets, or claim continuous uptime.

## Public entry points

- Landing: https://floodlens-ai-vert.vercel.app
- Demo: https://floodlens-judge.tail1bb8f1.ts.net/
- Review candidate: https://github.com/joa0lucassi/floodlens-ai/pull/4

The validated judge route is **Vercel landing page → Tailscale Funnel HTTPS → AWS ECS/Fargate → FloodLens API**. Vercel only provides the public project page and browser navigation. The authenticated API and a Tailscale sidecar run in the same ECS task when the service is active.

## Evidence register

| Date / source | Observed or reported | Limit |
| --- | --- | --- |
| 2026-10-13 repository AWS log | Earlier ECS/Fargate deployment processed a real development video with optional S3 enabled, then was scaled to zero | Historical storage-enabled validation; predates PR #4 judge mode |
| 2026-10-17 owner-assisted AWS/Tailscale validation | `floodlens-task:5` ran the application and Tailscale sidecar together; the application image was pinned to digest `sha256:74eba2477e09342edb873ba4f5e879df05e9399dc33267834598d70e17d72fa2` | Deployment evidence was observed interactively; the complete task definition JSON is not checked into this repository |
| 2026-10-17 external functional validation | Tailscale Funnel HTTPS, Basic Auth in an incognito session, and real model inference were successfully exercised against the AWS-hosted judge route | This validates that deployment session, not perpetual availability |
| 2026-10-17 network hardening | Public inbound TCP 8000 was removed from `floodlens-api-sg`; Funnel continued to work. The application trusted the local proxy through `FORWARDED_ALLOW_IPS=127.0.0.1` | Network configuration must be rechecked if the service or security group is later changed |
| 2026-10-17 secret handling | Judge password and Tailscale auth key were injected from AWS SSM SecureString parameters through the ECS execution role | Secret values are intentionally absent from source and this document |
| 2026-10-17 Vercel validation | Production landing page was redeployed; **Explore the system** was verified to open the judge URL | Landing availability does not imply that the stopped ECS backend is running |
| 2026-10-17 shutdown check | ECS service reached Desired=0, Running=0, Pending=0 after validation | The judge demo is expected to be unavailable while intentionally stopped |
| 2026-10-18 automated review | Landing returned HTTP 200 while the demo returned HTTP 502 from the review environment | Consistent with the backend having been intentionally scaled to zero; it does not invalidate the successful 2026-10-17 validation |

## Validated judge configuration

- ECS/Fargate task definition: `floodlens-task:5`.
- Application runtime: 1 vCPU / 2 GiB Fargate task, CPU inference.
- Application image: ECR image pinned by digest `sha256:74eba2477e09342edb873ba4f5e879df05e9399dc33267834598d70e17d72fa2`.
- Demo safeguards: Basic Auth required; HTTPS required; S3 disabled; shared history/risk endpoints disabled in authenticated demo mode.
- Tailscale: userspace sidecar in the same task, Funnel HTTPS forwarding locally to port 8000.
- Proxy trust: `FORWARDED_ALLOW_IPS=127.0.0.1`.
- Public network: no inbound security-group rule is required for TCP 8000.
- Credentials: supplied privately; no live credential belongs in source, URLs, screenshots, recordings, or public Devpost text.

## Remaining checks before judging

1. Reactivate the ECS service to the owner-approved `Desired=1` only for the required judge window.
2. Wait for `Desired=1`, `Running=1`, `Pending=0`, then confirm the final task still uses the intended task definition and pinned application image.
3. Recheck the Tailscale machine identity and hostname. Tailscale state is stored on the task's ephemeral volume, so a replacement task can create a hostname collision such as `floodlens-judge-1`; correct that before publishing an availability claim.
4. From an external/incognito session, verify landing → **Explore the system** → HTTPS → Basic Auth → one authorized real image/video inference.
5. Confirm TCP 8000 remains unavailable as a general internet entry point and that the local proxy trust setting remains restricted to `127.0.0.1`.
6. Keep the service active for the agreed judging period, then scale it back to zero after judging with separate authorization.

These are release checks, not evidence that the architecture was never validated. The end-to-end judge route was successfully validated on 2026-10-17 and then intentionally shut down to limit credit consumption.

## Privacy and resource limits in the reviewed source

Authenticated mode disables S3 and shared history/risk endpoints. Browser-session history is metadata. Image limits are 8 MiB and 16 million pixels; video limits are 48 MiB, 60 seconds and 2,073,600 pixels per frame. Upload reading has a total 60-second deadline. Video processing checks a 180-second cooperative budget between iterations; it cannot forcibly stop a stuck native decoder or model call. Do not market this as a hard execution limit or complete abuse protection.

## Known deployment limitation

The unresolved technical risk is the lack of a hard mechanism to terminate a native OpenCV decoder or model call that becomes stuck. The upload deadline and cooperative video budget do not provide hard cancellation. For the short controlled judge demo this risk is documented rather than hidden, but it remains a reason to keep PR #4 in draft until the owner decides whether to accept or address it.

A second operational limitation is Tailscale identity persistence: the sidecar state is ephemeral across full ECS task replacement. The current design deliberately avoids adding persistent storage solely for this short judge window; therefore hostname identity must be checked whenever the task is recreated.

## Costs and authorization

The service was intentionally scaled to zero after validation. When it is returned to `Desired=1`, Fargate and related AWS resources resume consuming promotional credits. Any activation window, paid-resource change, or added persistence remains a separate owner decision. Zero running service tasks stops the continuous Fargate task but does not by itself prove that every possible residual AWS charge is zero.
