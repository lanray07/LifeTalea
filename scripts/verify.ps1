$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    python -m pip install -r scripts/qa-requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'QA dependencies failed' }
    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Python tests failed' }
    python scripts/localize.py validate --strict
    if ($LASTEXITCODE -ne 0) { throw 'Localisation validation failed' }
    python scripts/localize.py check-release
    if ($LASTEXITCODE -ne 0) { throw 'Release locale review gate failed' }
    python scripts/validate_collateral.py
    if ($LASTEXITCODE -ne 0) { throw 'Website/store draft validation failed' }
    python scripts/polish_translations.py --check
    if ($LASTEXITCODE -ne 0) { throw 'Authored translation polish regressed' }
    node scripts/test_locale_match.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Browser locale matching failed' }
    node scripts/test_website_review_gate.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Website review gate failed' }
    node scripts/test_static_export.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Static-export prefetch check failed' }
    & .\android\gradlew.bat -p android --no-daemon testDebugUnitTest assembleDebug assembleRelease lintDebug
    if ($LASTEXITCODE -ne 0) { throw 'Android verification failed' }
    npm ci --prefix website
    if ($LASTEXITCODE -ne 0) { throw 'Website dependencies failed' }
    npm run build --prefix website
    if ($LASTEXITCODE -ne 0) { throw 'Website build failed' }
    python scripts/check_website.py
    if ($LASTEXITCODE -ne 0) { throw 'Website checks failed' }
} finally { Pop-Location }
