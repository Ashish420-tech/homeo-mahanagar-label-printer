!include "installer.nsi"

; Nullsoft Scriptable Install System (NSIS) script for Homeopathy Label Generator Installer

OutFile "HomeoLabelInstaller.exe"
InstallDir "$PROGRAMFILES\HomeoLabel"
RequestExecutionLevel admin

; Define the sections for installation
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File "..\src\homeo_label_printer_font_9_scaled.py"
    File "..\pyinstaller\homeo_label.spec"
    File "..\requirements.txt"
    File "..\resources\license.txt"
    File "..\resources\README.md.icon_placeholder"
    File "..\build_scripts\build_exe.ps1"
    File "..\build_scripts\build_exe.sh"
    ; Add any additional files needed for the installation
SectionEnd

; Create uninstaller
Section "Uninstall"
    Delete "$INSTDIR\homeo_label_printer_font_9_scaled.py"
    Delete "$INSTDIR\homeo_label.spec"
    Delete "$INSTDIR\requirements.txt"
    Delete "$INSTDIR\license.txt"
    Delete "$INSTDIR\README.md.icon_placeholder"
    Delete "$INSTDIR\build_exe.ps1"
    Delete "$INSTDIR\build_exe.sh"
    RMDir "$INSTDIR"
SectionEnd

; Installer interface settings
!define MUI_TITLE "Homeopathy Label Generator"
!define MUI_UNFINISHED_TITLE "Homeopathy Label Generator"
!define MUI_WELCOME_TEXT "Welcome to the Homeopathy Label Generator Installer."
!define MUI_FINISH_TEXT "Thank you for installing the Homeopathy Label Generator."
!define MUI_UNFINISHED_TEXT "Uninstallation is complete."

; Add a welcome page
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_PAGE_UNFINISH

; Set the uninstaller
!define MUI_UNFINISHED_TEXT "Uninstallation is complete."
!insertmacro MUI_UNFINISHED_PAGE

; Set the uninstaller
Section "Uninstall"
    Delete "$INSTDIR\HomeoLabelInstaller.exe"
    RMDir "$INSTDIR"
SectionEnd

; Define the uninstaller
!define MUI_UNFINISHED_TEXT "Uninstallation is complete."
!insertmacro MUI_UNFINISHED_PAGE

; Installer settings
!insertmacro MUI_LANGUAGE "English"