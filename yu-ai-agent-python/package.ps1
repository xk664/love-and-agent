# =============================================================================
# Yu AI Agent - Package Script for Cloud Deployment
# =============================================================================
# Usage: .\package.ps1
# Output: dist\yu-ai-agent-python.tar.gz
# =============================================================================

$ErrorActionPreference = "Stop"

# Configuration
$ProjectDir = $PSScriptRoot
$DistDir = Join-Path $ProjectDir "dist"
$PackageName = "yu-ai-agent-python"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutputFile = Join-Path $DistDir "$PackageName-$Timestamp.tar.gz"

# Clean dist directory
if (Test-Path $DistDir) {
    Remove-Item -Recurse -Force $DistDir
}
New-Item -ItemType Directory -Path $DistDir -Force | Out-Null

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Yu AI Agent - Package Builder" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project Directory: $ProjectDir" -ForegroundColor Gray
Write-Host "Output File: $OutputFile" -ForegroundColor Gray
Write-Host ""

# Files and directories to include (based on Dockerfile)
$IncludePaths = @(
    "main.py",
    "app",
    "config",
    "requirements.txt"
)

# Verify all required paths exist
Write-Host "Verifying required files..." -ForegroundColor Yellow
$MissingPaths = @()
foreach ($path in $IncludePaths) {
    $fullPath = Join-Path $ProjectDir $path
    if (-not (Test-Path $fullPath)) {
        $MissingPaths += $path
        Write-Host "  [MISSING] $path" -ForegroundColor Red
    } else {
        Write-Host "  [OK] $path" -ForegroundColor Green
    }
}

if ($MissingPaths.Count -gt 0) {
    Write-Host ""
    Write-Host "Error: Missing required files/folders:" -ForegroundColor Red
    $MissingPaths | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    exit 1
}

Write-Host ""
Write-Host "Creating package..." -ForegroundColor Yellow

# Create temporary staging directory
$TempDir = Join-Path $env:TEMP "$PackageName-$Timestamp"
if (Test-Path $TempDir) {
    Remove-Item -Recurse -Force $TempDir
}
New-Item -ItemType Directory -Path $TempDir -Force | Out-Null

try {
    # Copy files to staging directory
    foreach ($path in $IncludePaths) {
        $srcPath = Join-Path $ProjectDir $path
        $dstPath = Join-Path $TempDir $path

        if (Test-Path $srcPath -PathType Container) {
            Copy-Item -Recurse -Path $srcPath -Destination $dstPath
        } else {
            Copy-Item -Path $srcPath -Destination $dstPath
        }
        Write-Host "  Copied: $path" -ForegroundColor Gray
    }

    # Create tar.gz archive
    Write-Host ""
    Write-Host "Creating tar.gz archive..." -ForegroundColor Yellow

    # Use tar command (available on Windows 10+)
    Push-Location $TempDir
    try {
        tar -czf $OutputFile *
        if ($LASTEXITCODE -ne 0) {
            throw "tar command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Pop-Location
    }

    # Get package info
    $PackageInfo = Get-Item $OutputFile
    $SizeMB = [math]::Round($PackageInfo.Length / 1MB, 2)

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Package Created Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "File: $($PackageInfo.FullName)" -ForegroundColor White
    Write-Host "Size: $SizeMB MB" -ForegroundColor White
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Upload to cloud server:" -ForegroundColor White
    Write-Host "   scp $OutputFile user@server:/path/to/deploy/" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. On cloud server, extract and build:" -ForegroundColor White
    Write-Host "   tar -xzf $PackageName-$Timestamp.tar.gz" -ForegroundColor Gray
    Write-Host "   docker build -t $PackageName:latest ." -ForegroundColor Gray
    Write-Host ""
}
finally {
    # Cleanup temporary directory
    if (Test-Path $TempDir) {
        Remove-Item -Recurse -Force $TempDir
    }
}
