$srcImg = "C:\Users\jaydi\.gemini\antigravity\brain\d549a22f-d10e-459b-974b-61b3ae2f3440\ecopoints_icon_1779971145431.png"
$dest = Join-Path $PSScriptRoot "assets"

if (-not (Test-Path $dest)) {
    [void](New-Item -ItemType Directory -Path $dest)
}

@("favicon.png", "icon.png", "splash-icon.png", "adaptive-icon.png") | ForEach-Object {
    Copy-Item $srcImg (Join-Path $dest $_) -Force
}

Write-Host "Assets created:"
Get-ChildItem $dest | ForEach-Object { Write-Host "  $($_.Name) ($($_.Length) bytes)" }
