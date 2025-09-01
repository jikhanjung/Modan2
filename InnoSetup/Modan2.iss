#define AppVersion "0.1.4"
#define BuildNumber GetEnv('BUILD_NUMBER')

[Setup]
AppName=Modan2
AppVersion={#AppVersion}
DefaultDirName={commonpf}\PaleoBytes\Modan2
OutputDir=Output

OutputBaseFilename=Modan2_v{#AppVersion}_build{#BuildNumber}_Installer

[Files]
; Include main executable
Source: "..\dist\Modan2\Modan2.exe"; DestDir: "{app}"

; Include all other files and directories
Source: "..\dist\Modan2\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; Example datasets
Source: "..\ExampleDataset\*"; DestDir: "{%userprofile}\PaleoBytes\Modan2\ExampleDataset"; Flags: recursesubdirs createallsubdirs


[Run]
Filename: "{app}\Modan2.exe"; Flags: postinstall shellexec

[Code]
function InitializeSetup(): Boolean;
begin
  // Create a specific Start Menu group
  if not DirExists(ExpandConstant('{userprograms}\PaleoBytes')) then
    CreateDir(ExpandConstant('{userprograms}\PaleoBytes'));
  
  Result := True;
end;

[Icons]
Name: "{userprograms}\PaleoBytes\Modan2"; Filename: "{app}\Modan2.exe"
