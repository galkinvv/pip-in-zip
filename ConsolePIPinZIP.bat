@CD /D "%~dp0"
@PATH %~dp0;%PATH%
@PROMPT %CONSOLE_NAME_PLACEHOLDER% %PROMPT%
@start "%CONSOLE_NAME_PLACEHOLDER% from %~dp0" cmd /k "<nul set /p=Type ^"python^" to start interpreter or add packages by:  pip install package_name"