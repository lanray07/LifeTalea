$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }
    python scripts/localize.py validate
    if ($LASTEXITCODE -ne 0) { throw 'Localisation validation failed' }
    & .\android\gradlew.bat -p android --no-daemon testDebugUnitTest assembleDebug assembleRelease lintDebug
    if ($LASTEXITCODE -ne 0) { throw 'Android verification failed' }
    npm ci --prefix website
    if ($LASTEXITCODE -ne 0) { throw 'Website dependencies failed' }
    npm run build --prefix website
    if ($LASTEXITCODE -ne 0) { throw 'Website build failed' }
    python scripts/check_website.py
    if ($LASTEXITCODE -ne 0) { throw 'Website checks failed' }
} finally { Pop-Location }
