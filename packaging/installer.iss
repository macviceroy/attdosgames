#define AppName "ATT DOS GAMES Studio"
#define AppVersion "0.3.1"
#define AppExeName "ATT-DOS-GAMES-Studio.exe"

[Setup]
AppId={{CBB67AF2-37D2-40A3-B65A-89C7506139EA}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=ATT DOS GAMES
DefaultDirName={localappdata}\Programs\ATT DOS GAMES Studio
DefaultGroupName=ATT DOS GAMES Studio
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=ATT-DOS-GAMES-Studio-Setup-x64
Compression=lzma2/max
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}
WizardStyle=modern

[Files]
Source: "..\dist\ATT-DOS-GAMES-Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\ATT DOS GAMES Studio"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\ATT DOS GAMES Studio"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir ATT DOS GAMES Studio"; Flags: nowait postinstall skipifsilent
