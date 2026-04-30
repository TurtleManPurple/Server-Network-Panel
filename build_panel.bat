@echo off
title [TMP-Network] Build Panel

echo [TMP-Network] Compiling panel...

REM Compile with Java 21 target
javac --release 21 TMPNetworkPanel.java
if %errorlevel% neq 0 (
echo [TMP-Network] Compile FAILED
pause
exit /b
)

echo [TMP-Network] Creating JAR...

REM Create runnable JAR
jar cfe TMPNetworkPanel.jar TMPNetworkPanel *.class
if %errorlevel% neq 0 (
echo [TMP-Network] JAR build FAILED
pause
exit /b
)

echo [TMP-Network] Cleaning old class files...
del /q *.class

echo [TMP-Network] Build SUCCESS!
echo.
echo You can now run:
echo java -jar TMPNetworkPanel.jar
echo.

pause
