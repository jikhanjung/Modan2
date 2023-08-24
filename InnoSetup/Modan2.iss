#define AppVersion "0.1.0"
#define CurrentDate GetDateTimeString('yyyy-mm-dd', '-', ':')

[Setup]
AppName=Modan2
AppVersion={#AppVersion}
DefaultDirName={commonpf}\Modan2
OutputDir=Output

OutputBaseFilename=Modan2_v{#AppVersion}_Installer

[Files]
; Include main executable
Source: "..\dist\Modan2\Modan2.exe"; DestDir: "{app}"

; Include all other files and directories
Source: "..\dist\Modan2\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; Example datasets
Source: "..\ExampleDataset\*"; DestDir: "{%userprofile}\Modan2"; Flags: recursesubdirs createallsubdirs


[Run]
Filename: "{app}\Modan2.exe"; Flags: postinstall shellexec

[Code]
function InitializeSetup(): Boolean;
begin
  // Create a specific Start Menu group
  if not DirExists(ExpandConstant('{userprograms}\Modan2')) then
    CreateDir(ExpandConstant('{userprograms}\Modan2'));
  
  Result := True;
end;

[Icons]
Name: "{userprograms}\Modan2\Modan2"; Filename: "{app}\Modan2.exe"
