param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    throw "python command not found. Activate the project environment first."
}

$listenPattern = ':{0}\s+.*LISTENING\s+(\d+)$' -f $Port
$listenRows = netstat -ano | Select-String -Pattern $listenPattern
foreach ($row in $listenRows) {
    $text = (($row.Line -replace '\s+', ' ').Trim())
    $parts = $text.Split(' ')
    $pid = 0
    if ($parts.Length -gt 0) {
        [void][int]::TryParse($parts[-1], [ref]$pid)
    }
    if ($pid -gt 0) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Stopped old dashboard process PID=$pid"
        } catch {
            Write-Warning "Port $Port is still held by PID=$pid and could not be stopped automatically."
            throw
        }
    }
}

Write-Host "Starting dashboard: http://$ListenHost`:$Port"
& $pythonCmd.Source -m llm_wiki dashboard --host $ListenHost --port $Port
