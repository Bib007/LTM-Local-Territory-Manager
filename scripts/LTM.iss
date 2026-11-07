; Free per-user Windows installer. Build with Inno Setup 6.
#ifndef AppVersion
  #error AppVersion must be passed from GitHub Actions
#endif
#ifndef BuildDir
  #error BuildDir must point to the PyInstaller output
#endif
#ifndef OutputDir
  #error OutputDir must be provided
#endif

[Setup]
AppId={{B7195427-A9D7-4BE6-8BC6-5D629688DD97}
AppName=LTM - Local Territory Manager
AppVersion={#AppVersion}
AppVerName=LTM {#AppVersion}
DefaultDirName={localappdata}\Programs\LTM
DefaultGroupName=LTM
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=LTM-Windows-v{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\LTM.exe
SetupIconFile=distrikt\icon.ico
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "danish"; MessagesFile: "compiler:Languages\Danish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Opret genvej på skrivebordet"; GroupDescription: "Genveje"; Flags: unchecked

[Files]
Source: "{#BuildDir}\LTM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\LTM"; Filename: "{app}\LTM.exe"
Name: "{autodesktop}\LTM"; Filename: "{app}\LTM.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\LTM.exe"; Description: "Start LTM"; Flags: postinstall nowait skipifsilent
