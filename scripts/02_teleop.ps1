# テレオペの動作確認（リーダーを動かすとフォロワーが追従する）。Ctrl+C で終了
param(
    [switch]$WithCamera   # カメラ映像も一緒に表示したいとき
)
. "$PSScriptRoot\env.ps1"

$cliArgs = @(
    "--robot.type=so101_follower",
    "--robot.port=$env:ROBOT_PORT",
    "--robot.id=$env:ROBOT_ID",
    "--teleop.type=so101_leader",
    "--teleop.port=$env:TELEOP_PORT",
    "--teleop.id=$env:TELEOP_ID",
    "--robot.num_read_retries=10",
    "--teleop.num_read_retries=10"
)
if ($WithCamera) {
    $cliArgs += "--robot.cameras={ top: {type: opencv, index_or_path: $env:CAMERA_INDEX, width: 640, height: 480, fps: 30}}"
    $cliArgs += "--display_data=true"
}
& (Get-LeRobotCmd "lerobot-teleoperate") @cliArgs
