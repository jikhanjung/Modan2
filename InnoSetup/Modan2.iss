#define AppVersion "0.1.0"
#define CurrentDate GetDateTimeString('yyyy-mm-dd', '-', ':')

[Setup]
AppName=Modan2
AppVersion={#AppVersion}
DefaultDirName={commonpf}\Modan2
OutputDir=Output

OutputBaseFilename=Modan2_v{#AppVersion}_Installer

[Files]
Source: "..\dist\Modan2.exe"; DestDir: "{app}"

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
