# 通し実行（デモ・撮影用）
#   .\scripts\05_demo.ps1                        # 本番: 自動進行 + オーバーレイ表示
#   .\scripts\05_demo.ps1 -Instruction "歯ブラシは A と C だけ補充して"
#   .\scripts\05_demo.ps1 -DryRun                # ロボットを動かさず判定と計画だけ
#   .\scripts\05_demo.ps1 -Mock "A,C" -DryRun    # AI も呼ばない配線テスト
param(
    [string]$Instruction = "",
    [string]$Backend = "",
    [string]$Mock = "",
    [switch]$DryRun,
    [switch]$Confirm        # 再生ごとに Enter で確認したいとき
)
. "$PSScriptRoot\env.ps1"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$cliArgs = @("main.py", "--show")
if (-not $Confirm) { $cliArgs += "--auto" }
if ($DryRun) { $cliArgs += "--dry-run" }
if ($Instruction -ne "") { $cliArgs += @("--instruction", $Instruction) }
if ($Mock -ne "") { $cliArgs += @("--backend", "mock", "--mock-empty", $Mock) }
elseif ($Backend -ne "") { $cliArgs += @("--backend", $Backend) }

python @cliArgs
