param()
$base = 'http://127.0.0.1:8000'

function Send-Inbound($from, $body, $sid) {
    $encoded = "From=$([uri]::EscapeDataString($from))&To=%2B14092285773&Body=$([uri]::EscapeDataString($body))&MessageSid=$sid"
    try {
        Invoke-RestMethod -Method Post -Uri "$base/api/v1/sms/twilio/inbound" `
            -ContentType 'application/x-www-form-urlencoded' `
            -Body $encoded -TimeoutSec 15 | Out-Null
        Write-Host "  OK  $sid  |  $body"
    } catch {
        Write-Host "  ERR $sid : $($_.Exception.Message)"
    }
    Start-Sleep -Milliseconds 300
}

function Ensure-Farmer($fullName, $phone, $region, $village, $crop) {
    $payload = @{
        full_name=$fullName; phone_number=$phone; preferred_language='sw';
        region=$region; district=$region; village=$village;
        latitude=-3.369; longitude=36.8569; crop_type=$crop; is_active=$true
    } | ConvertTo-Json
    try {
        $f = Invoke-RestMethod -Method Post -Uri "$base/api/v1/farmers" -ContentType 'application/json' -Body $payload -TimeoutSec 10
        Write-Host "  created farmer: $fullName (id=$($f.id))"
    } catch {
        Write-Host "  farmer $fullName already exists or error: $($_.Exception.Message.Split([char]10)[0])"
    }
}

Write-Host ""
Write-Host "=== Creating demo farmers ==="
Ensure-Farmer 'Amina Hassan'    '+255710001001' 'Arusha'    'Usa River'  'Maize'
Ensure-Farmer 'John Mwenda'     '+255720002002' 'Dodoma'    'Kondoa'     'Sunflower'
Ensure-Farmer 'Grace Kiprotich' '+255730003003' 'Mwanza'    'Sengerema'  'Rice'
Ensure-Farmer 'Fatuma Osei'     '+255741004004' 'Kilimanjaro' 'Moshi'    'Coffee'
Ensure-Farmer 'Bakari Juma'     '+255752005005' 'Morogoro'  'Kilosa'     'Maize'
Ensure-Farmer 'Zawadi Baraka'   '+255763006006' 'Iringa'    'Mafinga'    'Wheat'
Ensure-Farmer 'Kamau Waweru'    '+255774007007' 'Mbeya'     'Rungwe'     'Tea'
Ensure-Farmer 'Salma Rashid'    '+255785008008' 'Tanga'     'Muheza'     'Cassava'
Ensure-Farmer 'Omar Siwa'       '+255796009009' 'Lindi'     'Liwale'     'Sesame'

# ─── RAIN_SEEN (mvua / manyunyu) ───────────────────────────────────────────
Write-Host ""
Write-Host "=== Amina Hassan - RAIN_SEEN x5 ==="
Send-Inbound '+255710001001' 'mvua nyingi sana leo'             'demo-rain-amina-001'
Send-Inbound '+255710001001' 'inanyesha sana usiku kucha'        'demo-rain-amina-002'
Send-Inbound '+255710001001' 'leo mvua kubwa imenyesha shambani' 'demo-rain-amina-003'
Send-Inbound '+255710001001' 'mvua bado haijaisha asubuhi'       'demo-rain-amina-004'
Send-Inbound '+255710001001' 'manyunyu makali yananyesha sasa'   'demo-rain-amina-005'

Write-Host ""
Write-Host "=== Salma Rashid - RAIN_SEEN x4 ==="
Send-Inbound '+255785008008' 'mvua imenyesha kwa saa mbili'      'demo-rain-salma-001'
Send-Inbound '+255785008008' 'inanyesha mvua kubwa sana'         'demo-rain-salma-002'
Send-Inbound '+255785008008' 'manyunyu mazito jana usiku'        'demo-rain-salma-003'
Send-Inbound '+255785008008' 'mvua nyingi shambani leo'          'demo-rain-salma-004'

# ─── FLOOD (mafuriko / flooding) ───────────────────────────────────────────
Write-Host ""
Write-Host "=== Bakari Juma - FLOOD x5 ==="
Send-Inbound '+255752005005' 'mafuriko yanakuja shambani'        'demo-flood-bakari-001'
Send-Inbound '+255752005005' 'mafuriko makubwa sana leo'         'demo-flood-bakari-002'
Send-Inbound '+255752005005' 'bonde lote limefurikwa maji'       'demo-flood-bakari-003'
Send-Inbound '+255752005005' 'mafuriko yameharibu mazao yangu'   'demo-flood-bakari-004'
Send-Inbound '+255752005005' 'flooding kali sana shambani leo'   'demo-flood-bakari-005'

# ─── STORM (dhoruba / upepo / kimbunga) ────────────────────────────────────
Write-Host ""
Write-Host "=== Grace Kiprotich - STORM x5 ==="
Send-Inbound '+255730003003' 'dhoruba inakuja kwa nguvu'         'demo-storm-grace-001'
Send-Inbound '+255730003003' 'upepo mkali na kimbunga leo'       'demo-storm-grace-002'
Send-Inbound '+255730003003' 'dhoruba kubwa imevunja miti'       'demo-storm-grace-003'
Send-Inbound '+255730003003' 'upepo wa nguvu sana usiku'         'demo-storm-grace-004'
Send-Inbound '+255730003003' 'kimbunga kikali kinakaribia'       'demo-storm-grace-005'

Write-Host ""
Write-Host "=== Kamau Waweru - STORM x4 ==="
Send-Inbound '+255774007007' 'dhoruba kubwa inakuja usiku'       'demo-storm-kamau-001'
Send-Inbound '+255774007007' 'upepo mkali umevunja nyumba'       'demo-storm-kamau-002'
Send-Inbound '+255774007007' 'kimbunga kali sana leo asubuhi'    'demo-storm-kamau-003'
Send-Inbound '+255774007007' 'dhoruba imeharibu shamba langu'    'demo-storm-kamau-004'

# ─── DRY_SOIL (ukame / kavu) ───────────────────────────────────────────────
Write-Host ""
Write-Host "=== Fatuma Osei - DRY_SOIL x5 ==="
Send-Inbound '+255741004004' 'ukame mkubwa shambani sasa'        'demo-dry-fatuma-001'
Send-Inbound '+255741004004' 'ardhi kavu kabisa hakuna mvua'     'demo-dry-fatuma-002'
Send-Inbound '+255741004004' 'ukame unaendelea wiki nzima'       'demo-dry-fatuma-003'
Send-Inbound '+255741004004' 'kavu sana mazao yanayokufa'        'demo-dry-fatuma-004'
Send-Inbound '+255741004004' 'drought kali hakuna maji kabisa'   'demo-dry-fatuma-005'

Write-Host ""
Write-Host "=== Omar Siwa - DRY_SOIL x4 ==="
Send-Inbound '+255796009009' 'ukame unaathiri mazao yangu'       'demo-dry-omar-001'
Send-Inbound '+255796009009' 'ardhi kavu na mimea inakufa'       'demo-dry-omar-002'
Send-Inbound '+255796009009' 'drought mbaya sana mwaka huu'      'demo-dry-omar-003'
Send-Inbound '+255796009009' 'ukame mkubwa hakuna mvua wiki mbili' 'demo-dry-omar-004'

# ─── PEST (wadudu / nzige) ─────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Zawadi Baraka - PEST x5 ==="
Send-Inbound '+255763006006' 'wadudu wanakula mazao yangu'       'demo-pest-zawadi-001'
Send-Inbound '+255763006006' 'nzige wengi wameingia shambani'    'demo-pest-zawadi-002'
Send-Inbound '+255763006006' 'wadudu wakubwa sana leo'           'demo-pest-zawadi-003'
Send-Inbound '+255763006006' 'nzige wameharibu nafaka zote'      'demo-pest-zawadi-004'
Send-Inbound '+255763006006' 'pest nyingi sana shambani sasa'    'demo-pest-zawadi-005'

# ─── HEAT (joto / kiangazi) → classified as UNKNOWN by feedback_parser ─────
Write-Host ""
Write-Host "=== John Mwenda - HEAT x5 (heat alert via signal service) ==="
Send-Inbound '+255720002002' 'joto kali sana leo shambani'       'demo-heat-john-001'
Send-Inbound '+255720002002' 'kiangazi kikali mazao yanafufuka'  'demo-heat-john-002'
Send-Inbound '+255720002002' 'joto kubwa sana temperatures leo'  'demo-heat-john-003'
Send-Inbound '+255720002002' 'kiangazi kimekuwa kali wiki hii'   'demo-heat-john-004'
Send-Inbound '+255720002002' 'joto la jua linachoma mazao yangu' 'demo-heat-john-005'

Write-Host ""
Write-Host "=== Checking results ==="
$feedback = Invoke-RestMethod -Uri "$base/api/v1/feedback" -TimeoutSec 10
Write-Host "Total feedback records: $($feedback.Count)"

$grouped = $feedback | Group-Object -Property feedback_type | Sort-Object Count -Descending
foreach ($g in $grouped) {
    Write-Host "  $($g.Name): $($g.Count) records"
}

$alerts = Invoke-RestMethod -Uri "$base/api/v1/messages/alerts" -TimeoutSec 10
$signalAlerts = $alerts | Where-Object { $_.alert_type -in @('rain','heat','storm','drought','flood','pest') }
Write-Host "Signal-triggered alerts: $($signalAlerts.Count)"
foreach ($a in $signalAlerts) {
    Write-Host "  [$($a.alert_type)] severity=$($a.severity) status=$($a.delivery_status) sms_sent=$($a.sent_at -ne $null)"
}
