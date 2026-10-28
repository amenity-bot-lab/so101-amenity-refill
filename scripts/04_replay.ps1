# 記録したエピソードを再生する（成功率チェック用）。replay.py を使う（ゆっくり開始・強めに握る・終了後も脱力しない）
#   .\scripts\04_replay.ps1 -Slot A              # pai/refill_A のエピソード 0
#   .\scripts\04_replay.ps1 -Slot A -Episode 2
#   .\scripts\04_replay.ps1 -Slot A -Episode 2 -GripBoost 30 -Check
param(
    [Parameter(Mandatory = $true)][ValidateSet("A", "B", "C")][string]$Slot,
    [int]$Episode = 0,
    [double]$GripBoost = -1,
    [switch]$Check
)
. "$PSScriptRoot\env.ps1"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$cliArgs = @("$ProjectRoot\replay.py", "--slot", $Slot, "--episode", "$Episode")
if ($GripBoost -ge 0) { $cliArgs += @("--grip-boost", "$GripBoost") }
if ($Check) { $cliArgs += "--check" }
python @cliArgs
