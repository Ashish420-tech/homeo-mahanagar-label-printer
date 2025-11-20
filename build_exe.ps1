# Usage: open PowerShell in this folder and run: .\build_exe.ps1
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Path $MyInvocation.MyCommand.Path -Parent
Push-Location $ProjectRoot

# 1) Create venv if missing
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
}

# 2) Activate venv (PowerShell)
. .\.venv\Scripts\Activate.ps1

# 3) Upgrade pip and install build deps
python -m pip install --upgrade pip
pip install pyinstaller pyqt5 pandas openpyxl reportlab pypiwin32

# 4) Clean previous build
Remove-Item -Recurse -Force .\build,.\\dist -ErrorAction SilentlyContinue

# 5) Build with PyInstaller (GUI app: --noconsole)
$Main = "homeo_label_printer_font_9_scaled.py"
$Name = "HomeoLabelPrinter"
# Add data: remedies.xlsx and records folder (if present). Format: "src;dest"
$addData = @()
if (Test-Path ".\remedies.xlsx") { $addData += "--add-data `".\remedies.xlsx;.`"" }
if (Test-Path ".\records") { $addData += "--add-data `".\records;records`"" }
$addDataStr = $addData -join " "

$icon = ""
if (Test-Path ".\app.ico") { $icon = "--icon .\app.ico" }

$cmd = "pyinstaller --noconsole --onefile --name $Name $icon $addDataStr `"$Main`""
Write-Host "Running: $cmd"
Invoke-Expression $cmd

# 6) Create minimal Inno Setup script for packaging (written to installer\homeo_installer.iss)
$InstallerDir = Join-Path $ProjectRoot "installer"
New-Item -ItemType Directory -Force -Path $InstallerDir | Out-Null

$exePath = Join-Path $ProjectRoot "dist\$Name.exe"
$issPath = Join-Path $InstallerDir "homeo_installer.iss"

$iss = @"
; filepath: $issPath
[Setup]
AppName=Homeo Label Printer
AppVersion=1.0
DefaultDirName={pf}\HomeoLabelPrinter
DefaultGroupName=HomeoLabelPrinter
OutputBaseFilename=HomeoLabelPrinter_Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "$exePath"; DestDir: "{app}"; Flags: ignoreversion
Source: "$ProjectRoot\remedies.xlsx"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "$ProjectRoot\records\*"; DestDir: "{app}\records"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Homeo Label Printer"; Filename: "{app}\$Name.exe"

[Run]
Filename: "{app}\$Name.exe"; Description: "Launch Homeo Label Printer"; Flags: nowait postinstall skipifsilent
"@

Set-Content -Path $issPath -Value $iss -Encoding UTF8
Write-Host "Build complete. EXE: $exePath"
Write-Host "Inno Setup script created at: $issPath"

Pop-Location