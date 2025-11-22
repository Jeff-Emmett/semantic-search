# Run this script in Windows PowerShell as Administrator
# This configures Windows Firewall and port forwarding for WSL

Write-Host "Setting up Windows Firewall rules for Semantic Search API..." -ForegroundColor Green

# Get WSL IP address
$wslIp = "172.22.168.84"
Write-Host "WSL IP Address: $wslIp" -ForegroundColor Cyan

# Add firewall rules for ports 8000 (API) and 8080 (HTTP server)
Write-Host "`nAdding firewall rules..." -ForegroundColor Yellow

# Remove existing rules if they exist
Remove-NetFirewallRule -DisplayName "WSL Semantic Search API" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "WSL Semantic Search HTTP" -ErrorAction SilentlyContinue

# Add new rules
New-NetFirewallRule -DisplayName "WSL Semantic Search API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL Semantic Search HTTP" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow

Write-Host "✓ Firewall rules added" -ForegroundColor Green

# Set up port forwarding from Windows to WSL
Write-Host "`nSetting up port forwarding..." -ForegroundColor Yellow

# Remove existing port proxies
netsh interface portproxy delete v4tov4 listenport=8000 | Out-Null
netsh interface portproxy delete v4tov4 listenport=8080 | Out-Null

# Add new port proxies
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIp

Write-Host "✓ Port forwarding configured" -ForegroundColor Green

# Show current port proxy configuration
Write-Host "`nCurrent port forwarding configuration:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host "`n✓ Setup complete!" -ForegroundColor Green
Write-Host "`nYou can now access the visualization at:" -ForegroundColor Yellow
Write-Host "  http://localhost:8080/graph_viewer_standalone.html" -ForegroundColor White
Write-Host "or" -ForegroundColor Yellow
Write-Host "  http://172.22.168.84:8080/graph_viewer_standalone.html" -ForegroundColor White
