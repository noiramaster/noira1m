$ServiceName = "NOIRA1M"
$ProjectDir = "C:\Users\aissa\noira1m"
$PythonExe = (Get-Command python).Source

# Create startup shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\NOIRA1M.lnk")
$Shortcut.TargetPath = $PythonExe
$Shortcut.Arguments = "-u `"$ProjectDir\launcher.py`""
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Save()

Write-Host "✅ NOIRA1M added to Windows Startup"
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Create your API keys (see KEYS_REQUIRED.md)"
Write-Host "2. Edit config\config.json with your keys"
Write-Host "3. Reboot your PC or run manually:"
Write-Host "   python launcher.py"
Write-Host ""
Write-Host "The dashboard will open at http://127.0.0.1:3001"
