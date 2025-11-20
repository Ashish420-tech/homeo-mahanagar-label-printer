<#
setup_package.ps1
Safe helper to prepare homeolabel package layout and data folder.
Run from project root: .\setup_package.ps1
#>

# ---------- Config ----------
$Root = (Get-Location).Path
$AppFile = Join-Path $Root "src\homeolabel\app.py"
$InitFile = Join-Path $Root "src\homeolabel\__init__.py"
$MainFile = Join-Path $Root "src\homeolabel\__main__.py"
$DataDir = Join-Path $Root "data"
$RecordsDir = Join-Path $DataDir "records"
$GitIgnore = Join-Path $Root ".gitignore"

# ---------- Helpers ----------
function Backup-IfExists($path) {
    if (Test-Path $path) {
        $ts = (Get-Date).ToString("yyyyMMddHHmmss")
        $bak = "$path.bak.$ts"
        Copy-Item $path $bak -Force
        Write-Host "Backed up $path -> $bak"
    }
}

Write-Host "Running setup_package.ps1 in: $Root" -ForegroundColor Cyan

# ---------- Create src/homeolabel if missing ----------
if (-not (Test-Path (Join-Path $Root "src\homeolabel"))) {
    New-Item -ItemType Directory -Path (Join-Path $Root "src\homeolabel") -Force | Out-Null
    Write-Host "Created src\homeolabel/ folder"
}

# ---------- Ensure __init__.py ----------
if (-not (Test-Path $InitFile)) {
    "from .app import HomeoLabelApp`n" | Set-Content -Path $InitFile -Encoding UTF8
    Write-Host "Created $InitFile"
} else {
    Write-Host "$InitFile already exists"
}

# ---------- Ensure __main__.py ----------
if (-not (Test-Path $MainFile)) {
    @"
import sys
from PyQt5 import QtWidgets
from .app import HomeoLabelApp

def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    w = HomeoLabelApp(scaling=1.0)
    w.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
"@ | Set-Content -Path $MainFile -Encoding UTF8
    Write-Host "Created $MainFile"
} else {
    Write-Host "$MainFile already exists"
}

# ---------- Create data and data\records ----------
if (-not (Test-Path $DataDir)) {
    New-Item -ItemType Directory -Path $DataDir | Out-Null
    Write-Host "Created data/ folder"
} else {
    Write-Host "data/ already exists"
}
if (-not (Test-Path $RecordsDir)) {
    New-Item -ItemType Directory -Path $RecordsDir | Out-Null
    Write-Host "Created data/records/ folder"
} else {
    Write-Host "data/records already exists"
}

# ---------- Move remedies* files to data/ ----------
$remedyPatterns = @("remedies.xlsx","remedies.xls","remedies.xlx","remedies_database.xlsx","remedies_database.csv","remedies_database.json")
foreach ($pat in $remedyPatterns) {
    $src = Join-Path $Root $pat
    if (Test-Path $src) {
        $dest = Join-Path $DataDir (Split-Path $pat -Leaf)
        Move-Item -Path $src -Destination $dest -Force
        Write-Host "Moved $pat -> data/"
    }
}

# ---------- Move existing records files into data/records ----------
if (Test-Path (Join-Path $Root "records")) {
    Write-Host "Moving files from records/ -> data/records/..."
    Get-ChildItem -Path (Join-Path $Root "records") -File -ErrorAction SilentlyContinue | ForEach-Object {
        Move-Item -Path $_.FullName -Destination $RecordsDir -Force
        Write-Host "  Moved $($_.Name) -> data/records/"
    }
    # try remove old records folder if now empty
    if ((Get-ChildItem -Path (Join-Path $Root "records") -Recurse -ErrorAction SilentlyContinue).Count -eq 0) {
        Remove-Item -Path (Join-Path $Root "records") -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Removed old empty records/ folder"
    }
} else {
    Write-Host "No root records/ folder found - skipping move"
}

# ---------- Inject DATA_DIR snippet into app.py if not present ----------
if (Test-Path $AppFile) {
    $appContent = Get-Content $AppFile -Raw
    if ($appContent -match "DATA_DIR\s*=") {
        Write-Host "app.py already contains DATA_DIR snippet - no injection needed"
    } else {
        # backup first
        Backup-IfExists $AppFile
        $snippet = @"
import os

# --- data directory resolution (project-root/data) ---
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))        # src/homeolabel
ROOT_DIR = os.path.abspath(os.path.join(PACKAGE_DIR, '..', '..'))    # repo root
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RECORDS_DIR = os.path.join(DATA_DIR, 'records')
os.makedirs(RECORDS_DIR, exist_ok=True)
# --- end data dir snippet ---
"@
        # Insert snippet after the first block of imports (simple prepend to be safe)
        $newContent = $snippet + "`n" + $appContent
        Set-Content -Path $AppFile -Value $newContent -Encoding UTF8
        Write-Host "Injected DATA_DIR snippet into src\homeolabel\app.py and backed up original."
    }
} else {
    Write-Host "app.py not found at $AppFile - please ensure your main app code is at src/homeolabel/app.py"
}

# ---------- Update .gitignore (backup old first) ----------
$gitignoreSnippet = @"
# Added by setup_package.ps1
# runtime data
data/
data/records/*.pdf
data/records/*_backup.json
data/records/label_preview.pdf
data/records/error_log.txt
# large dbs if any
data/remedies_database.*
"@

if (Test-Path $GitIgnore) {
    Backup-IfExists $GitIgnore
    Add-Content -Path $GitIgnore -Value "`n# ---- appended by setup_package.ps1 ----`n$gitignoreSnippet"
    Write-Host "Appended recommended entries to .gitignore (backup created)."
} else {
    $gitignoreSnippet | Set-Content -Path $GitIgnore -Encoding UTF8
    Write-Host "Created .gitignore with recommended entries."
}

# ---------- Final report ----------
Write-Host "`n--- Setup finished ---" -ForegroundColor Green
Write-Host "data/ contents:"
Get-ChildItem -Path $DataDir -Recurse | Format-Table -AutoSize
Write-Host "`nPlease review src\homeolabel\app.py and replace literal filenames like 'remedies.xlsx' 'records/...' with os.path.join(DATA_DIR, '...') or the variables RECORDS_DIR, DATA_DIR."
Write-Host "If you want automatic replacements, run: .\\setup_package.ps1 then request 'auto replace' to generate replacements."
Write-Host "`nNext recommended steps (run these):"
Write-Host "1) activate venv: .\\venv\\Scripts\\Activate"
Write-Host "2) install editable package: pip install -e ."
Write-Host "3) run tests: pytest -q"
Write-Host "4) run app: python -m homeolabel"
