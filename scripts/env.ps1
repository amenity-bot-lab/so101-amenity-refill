# プロジェクト直下の .env を読み込んで環境変数にする（他のスクリプトから . .\scripts\env.ps1 で呼ばれる）
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Host ".env がありません。.env.example をコピーして .env を作り、ポートやAPIキーを書いてください。" -ForegroundColor Yellow
    exit 1
}

Get-Content $EnvFile -Encoding UTF8 | ForEach-Object {
    $line = $_.Trim()
    if ($line -eq "" -or $line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -lt 1) { return }
    $key = $line.Substring(0, $idx).Trim()
    $val = $line.Substring($idx + 1).Trim().Trim('"')
    [Environment]::SetEnvironmentVariable($key, [Environment]::ExpandEnvironmentVariables($val), "Process")
}

# lerobot の CLI 置き場。空なら PATH 任せ
if ($env:LEROBOT_BIN) {
    $script:LR = $env:LEROBOT_BIN
} else {
    $script:LR = ""
}

function Get-LeRobotCmd([string]$name) {
    if ($script:LR) { return (Join-Path $script:LR "$name.exe") }
    return $name
}

# 既定値
if (-not $env:ROBOT_PORT)   { $env:ROBOT_PORT = "COM5" }
if (-not $env:ROBOT_ID)     { $env:ROBOT_ID = "my_follower" }
if (-not $env:TELEOP_PORT)  { $env:TELEOP_PORT = "COM4" }
if (-not $env:TELEOP_ID)    { $env:TELEOP_ID = "my_leader" }
if (-not $env:CAMERA_INDEX) { $env:CAMERA_INDEX = "0" }

Write-Host ("follower: {0} ({1})  leader: {2} ({3})  camera: {4}" -f $env:ROBOT_PORT, $env:ROBOT_ID, $env:TELEOP_PORT, $env:TELEOP_ID, $env:CAMERA_INDEX) -ForegroundColor Cyan
