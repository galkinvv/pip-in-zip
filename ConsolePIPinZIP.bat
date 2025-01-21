@CD /D "%~dp0"
@PATH %~dp0;%PATH%
@PROMPT PIPinZIP 3.14.0a4-win64 %PROMPT%
@start "PIPinZIP 3.14.0a4-win64 from %~dp0" cmd /k "<nul set /p=Type ^"python^" to start interpreter or add packages by:  pip install package_name"