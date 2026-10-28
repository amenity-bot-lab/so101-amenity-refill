# 区画1つ分の補充動作を記録する。
#   .\scripts\03_record.ps1 -Slot A              # pai/refill_A に 3 エピソード記録
#   .\scripts\03_record.ps1 -Slot B -Episodes 5
#   .\scripts\03_record.ps1 -Slot A -NoCamera     # カメラが原因で止まるときの切り分け用
#
# 記録中のキー操作:  → 今のエピソードを保存して次へ   ← 今のエピソードを捨てて撮り直し   Esc 終了（動画のエンコードが走る）
# 1エピソードの型:  ホームポーズで待つ → 補充元 $Slot 番の歯ブラシをつかむ → 区画 $Slot に置く → ホームポーズに戻る → →キー
param(
    [Parameter(Mandatory = $true)][ValidateSet("A", "B", "C")][string]$Slot,
    [int]$Episodes = 3,
    [int]$EpisodeTime = 30,     # 1エピソードの上限秒数（→キーで早めに終われる）
    [int]$ResetTime = 20,       # エピソード間の片付け時間（秒）
    [string]$Name = "",         # データセット名を変えたいとき（既定: pai/refill_<Slot>）
    [switch]$NoCamera,
    [switch]$Display            # rerun の表示を出す
)
. "$PSScriptRoot\env.ps1"

if ($Name -eq "") { $Name = "pai/refill_$Slot" }

$cliArgs = @(
    "--robot.type=so101_follower",
    "--robot.port=$env:ROBOT_PORT",
    "--robot.id=$env:ROBOT_ID",
    "--teleop.type=so101_leader",
    "--teleop.port=$env:TELEOP_PORT",
    "--teleop.id=$env:TELEOP_ID",
    "--robot.num_read_retries=10",
    "--teleop.num_read_retries=10",
    "--dataset.repo_id=$Name",
    "--dataset.num_episodes=$Episodes",
    "--dataset.single_task=Refill amenity tray slot $Slot with a toothbrush",
    "--dataset.episode_time_s=$EpisodeTime",
    "--dataset.reset_time_s=$ResetTime",
    "--dataset.push_to_hub=false",
    "--dataset.no_stamp=true"     # フォルダ名に日時を付けない（pai/refill_A のまま）
)
if (-not $NoCamera) {
    $cliArgs += "--robot.cameras={ top: {type: opencv, index_or_path: $env:CAMERA_INDEX, width: 640, height: 480, fps: 30}}"
}
if ($Display) { $cliArgs += "--display_data=true" }

$DatasetDir = Join-Path "$env:USERPROFILE\.cache\huggingface\lerobot" $Name
# 前回の記録が始まる前に失敗して、中身のない（data フォルダがない）フォルダだけ残っていたら消す
if ((Test-Path $DatasetDir) -and -not (Test-Path (Join-Path $DatasetDir "data"))) {
    Remove-Item $DatasetDir -Recurse -Force
    Write-Host "途中で失敗した空のフォルダを削除しました: $DatasetDir" -ForegroundColor Yellow
}
Write-Host "記録先: $DatasetDir" -ForegroundColor Green
Write-Host "同じ名前が既にあると失敗します。撮り直すときはそのフォルダを削除するか -Name で別名にしてください。" -ForegroundColor Yellow
& (Get-LeRobotCmd "lerobot-record") @cliArgs
