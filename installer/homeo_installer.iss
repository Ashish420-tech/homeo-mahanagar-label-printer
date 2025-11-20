; filepath: C:\Users\Ashish\Desktop\Newfolder2\homeolabel_project\installer\homeo_installer.iss
[Setup]
AppName=Homeo Label Printer
AppVersion=1.0
DefaultDirName={pf}\HomeoLabelPrinter
DefaultGroupName=HomeoLabelPrinter
OutputBaseFilename=HomeoLabelPrinter_Installer
Compression=lzma
SolidCompression=yes

[Files]
Source: "C:\Users\Ashish\Desktop\Newfolder2\homeolabel_project\dist\HomeoLabelPrinter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\Ashish\Desktop\Newfolder2\homeolabel_project\remedies.xlsx"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "C:\Users\Ashish\Desktop\Newfolder2\homeolabel_project\records\*"; DestDir: "{app}\records"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Homeo Label Printer"; Filename: "{app}\HomeoLabelPrinter.exe"

[Run]
Filename: "{app}\HomeoLabelPrinter.exe"; Description: "Launch Homeo Label Printer"; Flags: nowait postinstall skipifsilent
