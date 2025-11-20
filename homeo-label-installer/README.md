# Homeopathy Label Installer

## Overview
The Homeopathy Label Installer is designed to facilitate the installation of the Homeopathy Label Generator application. This application allows users to generate labels for homeopathic remedies, featuring a responsive UI and printing capabilities.

## Project Structure
The project is organized into several directories and files, each serving a specific purpose:

- **src/**: Contains the main application code.
  - `homeo_label_printer_font_9_scaled.py`: The core application logic, including UI and printing functionalities.

- **pyinstaller/**: Holds the PyInstaller specification file.
  - `homeo_label.spec`: Configuration for building the executable from the Python script.

- **installers/**: Contains installer scripts for different platforms.
  - **windows/**: Windows-specific installer files.
    - `installer.nsi`: NSIS script for creating the Windows installer.

- **build_scripts/**: Scripts to automate the build process.
  - `build_exe.ps1`: PowerShell script for building the executable.
  - `build_exe.sh`: Shell script for building the executable on Unix-like systems.

- **resources/**: Additional resources for the project.
  - `README.md.icon_placeholder`: Placeholder for resource documentation.
  - `license.txt`: Licensing information for the project.

- **requirements.txt**: Lists the Python dependencies required for the project.

- **setup.cfg**: Configuration file for packaging the project.

- **pyproject.toml**: Build system configuration file.

- **.gitignore**: Specifies files and directories to be ignored by Git.

- **LICENSE**: Full text of the project's license.

- **README.md**: Main documentation file for the project.

## Installation Instructions
To install the Homeopathy Label Generator, follow these steps:

1. **Download the Installer**: Obtain the installer executable from the releases section of the repository.

2. **Run the Installer**: Double-click the installer and follow the on-screen instructions to complete the installation.

3. **Launch the Application**: After installation, you can find the Homeopathy Label Generator in your applications menu.

## Usage
Once installed, you can use the Homeopathy Label Generator to create labels for homeopathic remedies. The application provides a user-friendly interface for entering remedy names, potencies, and other relevant information.

## License
This project is licensed under the terms specified in the `LICENSE` file. Please refer to it for details on usage and distribution rights.

## Contributing
Contributions to the Homeopathy Label Installer are welcome! Please follow the standard Git workflow for submitting issues and pull requests.

## Acknowledgments
Thank you for using the Homeopathy Label Generator. We hope it serves your needs effectively!