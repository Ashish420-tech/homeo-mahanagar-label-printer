#!/bin/bash

# This script builds the Homeopathy Label Generator executable using PyInstaller.

# Set the path to the Python script and the spec file
SCRIPT_PATH="../src/homeo_label_printer_font_9_scaled.py"
SPEC_FILE="../pyinstaller/homeo_label.spec"

# Create a build directory if it doesn't exist
BUILD_DIR="build"
mkdir -p $BUILD_DIR

# Activate the virtual environment if needed
# source /path/to/your/venv/bin/activate

# Run PyInstaller to build the executable
pyinstaller --onefile --clean --distpath $BUILD_DIR --workpath $BUILD_DIR/build --specpath $BUILD_DIR $SPEC_FILE

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully. Executable is located in the $BUILD_DIR directory."
else
    echo "Build failed. Please check the error messages above."
fi