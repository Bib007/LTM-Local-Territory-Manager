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

#if Pos("-beta.", AppVersion) > 0
  #define AppSuffix " Beta"
  #define InstallFolder "LTM-Beta"
  #define InstallId "{{B7195427-A9D7-4BE6-8BC6-5D629688DD98}"
#else
  #define AppSuffix ""
  #define InstallFolder "LTM"
  #define InstallId "{{B7195427-A9D7-4BE6-8BC6-5D629688DD97}"
#endif
#if Pos("-", AppVersion) > 0
  #define NumericVersion Copy(AppVersion, 1, Pos("-", AppVersion) - 1)
#else
  #define NumericVersion AppVersion
#endif
[Setup]
AppId={#InstallId}
AppName=LTM{#AppSuffix} - Local Territory Manager
AppVersion={#AppVersion}
VersionInfoVersion={#NumericVersion}
AppVerName=LTM {#AppVersion}
DefaultDirName={localappdata}\Programs\{#InstallFolder}
DefaultGroupName=LTM{#AppSuffix}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=LTM-Windows-v{#AppVersion}-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\LTM.exe
SetupIconFile={#BuildDir}\ltm.ico
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
; The selected setup language should also be LTM's initial UI language.
; LTM honours an existing browser choice, so upgrades never reset it.
Name: "{autoprograms}\LTM{#AppSuffix}"; Filename: "{app}\LTM.exe"; Parameters: "--language=da"; Languages: danish
Name: "{autoprograms}\LTM{#AppSuffix}"; Filename: "{app}\LTM.exe"; Parameters: "--language=en"; Languages: english
Name: "{autodesktop}\LTM{#AppSuffix}"; Filename: "{app}\LTM.exe"; Parameters: "--language=da"; Languages: danish; Tasks: desktopicon
Name: "{autodesktop}\LTM{#AppSuffix}"; Filename: "{app}\LTM.exe"; Parameters: "--language=en"; Languages: english; Tasks: desktopicon

[Run]
Filename: "{app}\LTM.exe"; Parameters: "--language=da"; Languages: danish; Description: "Start LTM"; Flags: postinstall nowait skipifsilent
Filename: "{app}\LTM.exe"; Parameters: "--language=en"; Languages: english; Description: "Launch LTM"; Flags: postinstall nowait skipifsilent
