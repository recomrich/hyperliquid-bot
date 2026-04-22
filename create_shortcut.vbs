Set oWS = WScript.CreateObject("WScript.Shell")
Dim desktopPath
desktopPath = oWS.SpecialFolders("Desktop")

Set oLink = oWS.CreateShortcut(desktopPath & "\Hyperliquid Bot + Claude.lnk")
oLink.TargetPath = "C:\Users\rsser\hyperliquid-bot\launch.bat"
oLink.WorkingDirectory = "C:\Users\rsser\hyperliquid-bot"
oLink.Description = "Lance le bot Hyperliquid et Claude Code"
oLink.WindowStyle = 1
oLink.Save

WScript.Echo "Raccourci créé sur le bureau !"
