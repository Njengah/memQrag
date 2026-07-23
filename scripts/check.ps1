# Run the standard memQrag verification checks locally (Windows/PowerShell).
#
# Mirrors .github/workflows/ci.yml and scripts/check.sh. See docs/DECISIONS.md
# ("CI And Local Check Scripts") for what each check covers and why.
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Write-Output "==> Backend: ruff lint"
python -m ruff check .

Write-Output "==> Backend: ruff format check"
python -m ruff format --check .

Write-Output "==> Backend: pytest"
python -m pytest

Write-Output "==> Frontend: lint (oxlint)"
Push-Location ui
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { throw "npm run lint failed" }
} finally {
    Pop-Location
}

Write-Output "==> Frontend: build (tsc + vite build)"
Push-Location ui
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
} finally {
    Pop-Location
}

Write-Output "All checks passed."
