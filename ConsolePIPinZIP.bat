@CD /D "%~dp0"
@PATH %~dp0;%PATH%
@PROMPT PIPinZIP 3.8.20-fix64 %PROMPT%
@start "PIPinZIP 3.8.20-fix64 from %~dp0" cmd /k "<nul set /p=Type ^"python^" to start interpreter or add packages by:  pip install package_name"