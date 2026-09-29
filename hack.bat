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

function Show-PersistedPatient {
    param (
        $patient,
        [int]$index = 1,
        [int]$total = 1
    )

    $displayId = if ($patient.synthetic_patient_id) { $patient.synthetic_patient_id } else { $patient.patient_id }
    if ($displayId -like "SYN-*") {
        $displayId = "P-" + $displayId.Substring(4)
    }
    $ageVal = if ($patient.age_range) { $patient.age_range } elseif ($patient.age) { "$($patient.age) yrs" } else { "N/A" }
    $phoneVal = if ($patient.phone_number) { $patient.phone_number } else { $patient.phone }
    $aadhaarVal = if ($patient.aadhaar_number) { $patient.aadhaar_number } else { $patient.aadhaar }
    $medsVal = if ($patient.medicines -is [array]) { $patient.medicines -join ', ' } else { $patient.medicines }

    Write-Host "  [SYNTHETIC TWIN DECOY $index / $total] Synthetic Patient ID: $displayId" -ForegroundColor Yellow
    Write-Host "  - Synthetic Decoy Name:  $($patient.name)" -ForegroundColor White
    Write-Host "  - Synthetic Patient ID:  $displayId" -ForegroundColor Yellow
    Write-Host "  - Age Range:             $ageVal" -ForegroundColor White
    Write-Host "  - Gender:                $($patient.gender)" -ForegroundColor White
    Write-Host "  - Synthetic Phone:       $phoneVal" -ForegroundColor White
    Write-Host "  - Synthetic Aadhaar:     $aadhaarVal" -ForegroundColor White
    Write-Host "  - Synthetic Email:       $($patient.email)" -ForegroundColor White
    Write-Host "  - Decoy Disease:         $($patient.disease)" -ForegroundColor White
    Write-Host "  - Decoy Diagnosis:       $($patient.diagnosis)" -ForegroundColor White
    Write-Host "  - Treatment Pattern:     $($patient.treatment_pattern)" -ForegroundColor White
    Write-Host "  - Medicines:             $medsVal" -ForegroundColor White
    Write-Host "  - Location Address:      $($patient.address)" -ForegroundColor White
}

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
        Write-Host "======================================================================" -ForegroundColor Cyan
        try {
            $headers = @{ "X-Session-Id" = "hacker-single-probe"; "X-Device" = "adversary-terminal" }
            $res = Invoke-RestMethod -Uri "$target/api/patients?limit=1" -Method Get -Headers $headers -TimeoutSec 15
            $p = @($res.patients)[0]

            if ($null -eq $p -or [string]::IsNullOrWhiteSpace([string]$p.synthetic_patient_id)) {
                Write-Host "No persisted synthetic twin was available" -ForegroundColor Yellow
                break
            }

            Write-Host "`n[+] [HACKER RESULT]: 1 patient record dumped successfully`n" -ForegroundColor Green
            Show-PersistedPatient $p
            Write-Host "  --------------------------------------------------`n" -ForegroundColor DarkCyan
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
            $pts = @($res.patients)
            if ($pts.Count -eq 0) {
                Write-Host "No persisted synthetic twin was available" -ForegroundColor Yellow
                break
            }
            Write-Host "`n[+] [HACKER EXFILTRATION RESULT]: $($pts.Count) patient records dumped successfully`n" -ForegroundColor Green
            $i = 1
            foreach ($p in $pts) {
                Show-PersistedPatient $p $i $pts.Count
                $i++
            }
            Write-Host "  --------------------------------------------------`n" -ForegroundColor DarkCyan
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
            $probe = Invoke-RestMethod -Uri "$target/api/patients?limit=1" -Method Get -Headers $headers -TimeoutSec 15
            $p = @($probe.patients)[0]
            if ($null -eq $p -or [string]::IsNullOrWhiteSpace([string]$p.synthetic_patient_id)) {
                Write-Host "No persisted synthetic twin was available" -ForegroundColor Yellow
                break
            }
            Write-Host "`n[+] [SQL INJECTION EXTRACTION PAYLOAD RECEIVED]:" -ForegroundColor Green
            Show-PersistedPatient $p
            Write-Host "  --------------------------------------------------`n" -ForegroundColor DarkCyan
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
            $probe = Invoke-RestMethod -Uri "$target/api/patients?limit=1" -Method Get -Headers $headers -TimeoutSec 10
            $p = @($probe.patients)[0]
            if ($null -eq $p -or [string]::IsNullOrWhiteSpace([string]$p.synthetic_patient_id)) {
                Write-Host "No persisted synthetic twin was available" -ForegroundColor Yellow
                break
            }
            Write-Host "  --------------------------------------------------" -ForegroundColor DarkCyan
            Write-Host "  [EXTRACTED EHR PAYLOAD AFTER BRUTE FORCE]:" -ForegroundColor Yellow
            Show-PersistedPatient $p
            Write-Host "  --------------------------------------------------`n" -ForegroundColor DarkCyan
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

        try {
            $headers = @{ "X-Session-Id" = "hacker-enum-probe"; "X-Device" = "adversary-terminal" }
            $res = Invoke-RestMethod -Uri "$target/api/patients?limit=$count" -Method Get -Headers $headers -TimeoutSec 10
            $pts = @($res.patients)
            if ($pts.Count -eq 0) {
                Write-Host "No persisted synthetic twin was available" -ForegroundColor Yellow
                break
            }
            Write-Host "`n[+] [ENUMERATION RESULT]: $($pts.Count) patient records returned`n" -ForegroundColor Green
            $i = 1
            foreach ($p in $pts) {
                Show-PersistedPatient $p $i $pts.Count
                $i++
            }
            Write-Host "  --------------------------------------------------`n" -ForegroundColor DarkCyan
        } catch {
            Write-Host "[-] Enumeration failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    default {
        Show-Help
    }
}
