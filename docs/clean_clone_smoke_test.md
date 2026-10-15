# Clean-clone reproducibility smoke test (local Docker)

This procedure tests whether a **fresh Git checkout** can start the FloodLens AI API/dashboard given a legitimately obtained official MultiDomain checkpoint. It does not require AWS, S3 credentials, or any training/evaluation datasets.

> **Model distribution rights are still under review.** This procedure copies the developer's existing local checkpoint for a local smoke test. Do not publish it or share the trained weights publicly until the data provenance/permissions review is resolved. See [data provenance audit](data_provenance_and_model_release.md).

## Requirements

- Windows PowerShell 7+ (commands below), Docker Desktop running, Git installed.
- Original project working copy and its verified `models/flood_segmentation/best.pt`.
- Free local TCP port **8002** (the existing project may continue to use 8001).
- Docker image build requires internet access to download dependencies if they are not cached.

## 1. Clone in a separate directory

Run from the **original FloodLens project directory**:

```powershell
$originalRoot = (Get-Location).Path
$modelSource = Join-Path $originalRoot "models\flood_segmentation\best.pt"
if (-not (Test-Path -LiteralPath $modelSource)) {
    throw "Checkpoint missing: $modelSource"
}

$testRoot = Join-Path $env:TEMP ("floodlens-clean-" + [guid]::NewGuid().ToString("N").Substring(0,8))
git clone --depth 1 --branch main https://github.com/joa0lucassi/floodlens-ai.git $testRoot
if ($LASTEXITCODE -ne 0) { throw "Git clone failed" }
```

## 2. Add only the local official model checkpoint

```powershell
$modelDestinationDir = Join-Path $testRoot "models\flood_segmentation"
New-Item -ItemType Directory -Force -Path $modelDestinationDir | Out-Null
Copy-Item -LiteralPath $modelSource -Destination (Join-Path $modelDestinationDir "best.pt")

Push-Location $testRoot
python scripts/verify_official_model.py
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Checkpoint verification failed" }
```

The expected SHA-256 is:

`82D7BE3E54BA74628F7BE86334CA10E8F4D4B7327AC224FC7787EFDE5E1050B3`

The verifier needs only Python's standard library, and will exit nonzero if the official checkpoint does not match.

## 3. Build and start the standalone local Docker container

```powershell
docker build -t floodlens-clean-smoke .
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Docker build failed" }

docker run -d --rm --name floodlens-clean-smoke -p 127.0.0.1:8002:8000 floodlens-clean-smoke
if ($LASTEXITCODE -ne 0) { Pop-Location; throw "Docker run failed; check port 8002 and container name" }
```

Allow the model several seconds to load; then test:

```powershell
Invoke-RestMethod http://127.0.0.1:8002/health
$response = Invoke-WebRequest http://127.0.0.1:8002/ -UseBasicParsing
$response.StatusCode
$response.Content -match "See beyond the surface"
```

Expected: `/health` returns `status: healthy`, `model_loaded: true`, `s3_enabled: false`; `/ ` returns **200**, and the dashboard text match returns **True**.

For a functional test, open `http://127.0.0.1:8002/` in the browser and analyze a locally owned/reusable image or short video. The model must produce an actual result, not just a healthy status. Do **not** rerun the frozen holdout as part of setup validation.

## 4. Cleanup

```powershell
docker rm -f floodlens-clean-smoke
Pop-Location
# The separate $testRoot directory is left in place for inspection.
# To remove after confirming it contains only disposable clone files:
# Remove-Item -LiteralPath $testRoot -Recurse -Force
```

Avoid deleting the original project or its checkpoint; the `$testRoot` directory is disposable.

## Verification log — 2026-10-15

**Status: PASS — developer-reported local clean-clone smoke test.**

The project developer followed this procedure with a separate checkout of GitHub `main` and reported:

1. Checkpoint verified against the frozen official SHA-256 with `scripts/verify_official_model.py`: **PASS**.
2. Fresh Docker image built and started successfully on localhost port **8002**: **PASS**.
3. `GET http://127.0.0.1:8002/health` returned **`status: healthy`**, **`model_loaded: True`**, **`s3_enabled: False`**, **`version: 0.7.0`**: **PASS**.
4. Opened the dashboard at port 8002 and completed a real upload/video analysis: **PASS, as reported by the developer**. No new detailed numerical metrics or logs were provided for this run.

This supports **local reproducibility of inference and the UI with an authorized model file supplied separately**. It does **not** demonstrate that a public clone without weights is self-contained, establish production readiness, validate new model accuracy, or resolve third-party distribution rights.

## Notes

- The public GitHub repository intentionally excludes `*.pt` and the `models` directory; therefore a fresh checkout **cannot be built until a legitimately obtained model file is placed at the documented path**.
- `Dockerfile` copies `src/` and `models/` into the container. It intentionally does not bundle local `data/` or `runs/`.
- `/risk/latest` relies on an optional local JSON file and may return 404; the dashboard and `/analyze/image`, `/analyze/video` are the relevant clean-clone smoke test endpoints.
- Without S3 configuration, analysis history is only retained during the current browser session and isn't persisted.
- This is a **smoke test**, not a formal independent-model evaluation or a production security review.
