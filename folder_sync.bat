@echo off
setlocal

:: Define source and destination folders
set "SOURCE_FOLDER=D:\Memories"
set "DESTINATION_FOLDER=E:\Memories"

:: Check if source folder exists
if not exist "%SOURCE_FOLDER%" (
    echo Source folder does not exist: %SOURCE_FOLDER%
    pause
    exit /b 1
)

:: Check if destination folder exists, if not create it
if not exist "%DESTINATION_FOLDER%" (
    echo Destination folder does not exist. Creating: %DESTINATION_FOLDER%
    mkdir "%DESTINATION_FOLDER%"
)

:: Use robocopy to sync folders
robocopy "%SOURCE_FOLDER%" "%DESTINATION_FOLDER%" /E /MIR /XO /NP /R:3 /W:5

:: Check robocopy exit code
if %ERRORLEVEL% GEQ 8 (
    echo Error during synchronization. Robocopy returned error code: %ERRORLEVEL%
    pause
    exit /b 1
) else (
    echo Synchronization completed successfully.
)

endlocal
pause