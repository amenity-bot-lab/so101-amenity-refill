# カメラの番号を調べる。出力の最後の数字が index_or_path / CAMERA_INDEX になる
. "$PSScriptRoot\env.ps1"
& (Get-LeRobotCmd "lerobot-find-cameras") opencv
Write-Host ""
Write-Host "各カメラのテスト画像は outputs/captured_images/ に保存されます。真上カメラの番号を .env の CAMERA_INDEX に書いてください。" -ForegroundColor Green
