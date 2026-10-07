$ErrorActionPreference = "Stop"

Clear-Host

$Region = "us-east-1"
$Repository = "floodlens-api"
$LocalImage = "floodlens-api:final"

Write-Host ""
Write-Host "========================================="
Write-Host "       FloodLens AI - AWS Deploy"
Write-Host "========================================="
Write-Host ""

Write-Host "[1/4] Getting AWS account information..."

$AccountId = aws sts get-caller-identity `
    --query Account `
    --output text

if (-not $AccountId) {
    throw "Could not retrieve AWS Account ID."
}

$Registry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$RemoteImage = "$Registry/$Repository`:latest"

Write-Host "[2/4] Authenticating Docker with Amazon ECR..."

aws ecr get-login-password `
    --region $Region |
    docker login `
        --username AWS `
        --password-stdin $Registry

Write-Host ""
Write-Host "[3/4] Preparing FloodLens Docker image..."

docker tag `
    $LocalImage `
    $RemoteImage

Write-Host ""
Write-Host "[4/4] Uploading FloodLens AI to AWS..."
Write-Host ""

docker push $RemoteImage

Write-Host ""
Write-Host "Checking image in Amazon ECR..."
Write-Host ""

aws ecr describe-images `
    --repository-name $Repository `
    --region $Region `
    --query "imageDetails[*].{Tag:imageTags,Digest:imageDigest,Pushed:imagePushedAt}" `
    --output table

Write-Host ""
Write-Host "========================================="
Write-Host " FloodLens AI successfully sent to AWS!"
Write-Host "========================================="
Write-Host ""