#ifndef AppVer
  #define AppVer "1.2.0"
#endif

[Setup]
AppName=Omega
AppVersion={#AppVer}
DefaultDirName={autopf}\Omega
DefaultGroupName=Omega
OutputDir=..\installer_out
OutputBaseFilename=Omega-Setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\Omega.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"

[Files]
Source: "..\dist\Omega\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Omega"; Filename: "{app}\Omega.exe"
Name: "{autodesktop}\Omega"; Filename: "{app}\Omega.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Omega.exe"; Description: "Abrir o Omega"; Flags: nowait postinstall skipifsilent
