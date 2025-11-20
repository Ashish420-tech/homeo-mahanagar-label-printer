# PowerShell script to build the Homeopathy Label Generator executable using PyInstaller

# Set the path to the Python executable
$pythonPath = "python"  # Adjust this if Python is not in your PATH

# Set the path to the PyInstaller spec file
$specFile = ".\pyinstaller\homeo_label.spec"

# Set the output directory for the build
$outputDir = ".\dist"

# Create the output directory if it doesn't exist
if (-Not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

# Run PyInstaller to build the executable
& $pythonPath -m PyInstaller $specFile --clean --onefile --distpath $outputDir

# Check if the build was successful
if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed successfully. Executable is located in $outputDir"
} else {
    Write-Host "Build failed. Please check the output for errors."
}