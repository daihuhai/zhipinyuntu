# Zhipin Yuntu Admin API Test Script (ASCII-only to avoid encoding issues)
$ErrorActionPreference = "Continue"
$BASE = "http://localhost:8000/api/v1"
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Send-Request {
    param([string]$Method, [string]$Url, [string]$Body = $null, [string]$Token = $null)
    $headers = @{}
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $result = [PSCustomObject]@{ Status = 0; TimeMs = 0; Body = ""; Error = "" }
    try {
        $params = @{ Uri = $Url; Method = $Method; Headers = $headers; UseBasicParsing = $true; TimeoutSec = 15 }
        if ($Body) { $params["ContentType"] = "application/json"; $params["Body"] = $Body }
        $resp = Invoke-WebRequest @params -ErrorAction Stop
        $sw.Stop()
        $result.Status = [int]$resp.StatusCode
        $result.Body = $resp.Content
        $result.TimeMs = $sw.ElapsedMilliseconds
    } catch {
        $sw.Stop()
        $result.TimeMs = $sw.ElapsedMilliseconds
        if ($_.Exception.Response) {
            $result.Status = [int]$_.Exception.Response.StatusCode
            try { $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream()); $result.Body = $sr.ReadToEnd() } catch { $result.Body = "(no body)" }
        } else { $result.Status = 0; $result.Error = $_.Exception.Message }
    }
    return $result
}

function Trunc {
    param([string]$text, [int]$maxLen = 400)
    if ($null -eq $text) { return "" }
    if ($text.Length -le $maxLen) { return $text }
    return $text.Substring(0, $maxLen) + "...(truncated)"
}

Write-Host "========================================"
Write-Host " Zhipin Yuntu Admin API Test Report"
Write-Host " Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host " Backend: http://localhost:8000"
Write-Host "========================================"
Write-Host ""

# 1. Login
Write-Host "[1/7] Login (admin / admin123) ..."
$loginBody = @{account='admin'; password='admin123'} | ConvertTo-Json -Compress
$login = Send-Request -Method Post -Url "$BASE/auth/login" -Body $loginBody
Write-Host "  HTTP Status: $($login.Status)"
Write-Host "  Time:        $($login.TimeMs) ms"
Write-Host "  Response:    $(Trunc $login.Body 500)"
Write-Host ""

$token = $null
if ($login.Status -eq 200) {
    try {
        $lj = $login.Body | ConvertFrom-Json
        if ($lj.data -and $lj.data.access_token) { $token = $lj.data.access_token }
        elseif ($lj.access_token) { $token = $lj.access_token }
    } catch {}
}
if (-not $token) { Write-Host "!! Login failed - no token. Subsequent tests run without auth." }
else { Write-Host "  >> Got token: $($token.Substring(0,[Math]::Min(30,$token.Length)))..." }
Write-Host ""

# Test list
$tests = @(
    @{Idx=2; Name="Dashboard Stats";    Method="GET"; Url="$BASE/admin/dashboard"},
    @{Idx=3; Name="Users List";         Method="GET"; Url="$BASE/admin/users?page=1&size=10"},
    @{Idx=4; Name="Resumes List";       Method="GET"; Url="$BASE/admin/resumes?page=1&size=10"},
    @{Idx=5; Name="Jobs List";          Method="GET"; Url="$BASE/admin/jobs?page=1&size=10"},
    @{Idx=6; Name="Logs List";          Method="GET"; Url="$BASE/admin/logs?page=1&size=10"},
    @{Idx=7; Name="Current User Info";  Method="GET"; Url="$BASE/auth/me"}
)

$results = @()
foreach ($t in $tests) {
    Write-Host "[$($t.Idx)/7] $($t.Name) ..."
    Write-Host "  Request: $($t.Method) $($t.Url)"
    $r = Send-Request -Method $t.Method -Url $t.Url -Token $token
    Write-Host "  HTTP Status: $($r.Status)"
    Write-Host "  Time:        $($r.TimeMs) ms"
    if ($r.Error) { Write-Host "  Error:       $($r.Error)" }
    Write-Host "  Response:    $(Trunc $r.Body 600)"
    Write-Host ""
    $results += [PSCustomObject]@{ Index=$t.Idx; Name=$t.Name; Method=$t.Method; Url=$t.Url; Status=$r.Status; TimeMs=$r.TimeMs; Body=$r.Body }
    Start-Sleep -Milliseconds 100
}

# Summary table
Write-Host ""
Write-Host "========================================"
Write-Host " Test Results Summary"
Write-Host "========================================"
$all = @([PSCustomObject]@{Index=1; Name="Login"; Method="POST"; Url="$BASE/auth/login"; Status=$login.Status; TimeMs=$login.TimeMs}) + $results
$all | Format-Table -AutoSize -Property Index, Name, Status, TimeMs, @{Name="Url"; Expression={$_.Url.Replace($BASE,'...')}}

# Key checks
Write-Host ""
Write-Host "========================================"
Write-Host " Key Checks"
Write-Host "========================================"
if ($login.Status -eq 200 -and $token) { Write-Host "[OK]   Login success - got access_token" }
else { Write-Host "[FAIL] Login failed (status $($login.Status))" }

$errorCodes = @(403, 404, 422, 500)
foreach ($r in $results) {
    if ($r.Status -in $errorCodes) { Write-Host "[WARN] $($r.Name) returned $($r.Status)" }
    elseif ($r.Status -eq 0) { Write-Host "[FAIL] $($r.Name) request failed (no response)" }
    else { Write-Host "[OK]   $($r.Name) status $($r.Status)" }
}
foreach ($r in $results) {
    if ($r.TimeMs -gt 3000) { Write-Host "[WARN] $($r.Name) response time $($r.TimeMs) ms > 3s" }
}

# Dashboard completeness
$dash = $results | Where-Object { $_.Index -eq 2 } | Select-Object -First 1
if ($dash -and $dash.Status -eq 200) {
    try {
        $dj = $dash.Body | ConvertFrom-Json
        $dd = if ($dj.data) { $dj.data } else { $dj }
        $keys = ($dd | Get-Member -MemberType NoteProperty).Name
        Write-Host "[INFO] Dashboard fields: $($keys -join ', ')"
        $need = @("user","resume","job","match")
        foreach ($n in $need) {
            $hit = $keys | Where-Object { $_ -match $n }
            if ($hit) { Write-Host "[OK]   Dashboard has '$n' field(s): $($hit -join ',')" }
            else { Write-Host "[WARN] Dashboard missing '$n' field" }
        }
    } catch { Write-Host "[WARN] Dashboard response parse failed" }
}

# Users pagination
$ul = $results | Where-Object { $_.Index -eq 3 } | Select-Object -First 1
if ($ul -and $ul.Status -eq 200) {
    try {
        $uj = $ul.Body | ConvertFrom-Json
        $ud = if ($uj.data) { $uj.data } else { $uj }
        $ukeys = ($ud | Get-Member -MemberType NoteProperty).Name
        Write-Host "[INFO] Users fields: $($ukeys -join ', ')"
        if ($ukeys -match "total") { Write-Host "[OK]   Users has 'total' field" } else { Write-Host "[WARN] Users missing 'total' field" }
        if ($ukeys -match "items|list|records") { Write-Host "[OK]   Users has items/list/records field" } else { Write-Host "[WARN] Users missing items/list/records field" }
    } catch { Write-Host "[WARN] Users response parse failed" }
}

Write-Host ""
Write-Host "========================================"
Write-Host " Test Complete"
Write-Host "========================================"
