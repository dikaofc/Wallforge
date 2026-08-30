; Inno Setup script for Wallforge
; Builds Wallforge-Setup.exe from the PyInstaller --onedir output.

#define MyAppName "Wallforge"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Dika"
#define MyAppExeName "Wallforge.exe"
#define SourceDir "C:\Users\RootDika\Documents\WallpaperForgeLive\dist\Wallforge"

[Setup]
AppId={{8F2A1C3E-2B7A-4E1D-9C5B-1A2B3C4D5E6F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=C:\Users\RootDika\Documents\WallpaperForgeLive\installer\out
OutputBaseFilename={#MyAppName}-Setup
SetupIconFile=C:\Users\RootDika\Documents\WallpaperForgeLive\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Main application (onedir bundle)
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; VLC portable (extracted to installer/vlc)
Source: "C:\Users\RootDika\Documents\WallpaperForgeLive\installer\vlc\*"; DestDir: "{app}\vlc"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
