"""Run local non-device checks and retain actual exit codes/output for the review bundle.

Use an interpreter with scripts/qa-requirements.txt installed. Android build,
physical instrumentation, screenshot rendering and APK inspection run separately.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, subprocess, sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / 'deliverables/android/build-logs'

def main():
    checks = [
        ('python-tests', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('app-locales', [sys.executable, 'scripts/localize.py', 'validate', '--strict']),
        ('release-locales', [sys.executable, 'scripts/localize.py', 'check-release']),
        ('collateral', [sys.executable, 'scripts/validate_collateral.py']),
        ('polish', [sys.executable, 'scripts/polish_translations.py', '--check']),
        ('browser-locales', ['node', 'scripts/test_locale_match.cjs']),
        ('website-gate', ['node', 'scripts/test_website_review_gate.cjs']),
        ('static-export', ['node', 'scripts/test_static_export.cjs']),
        ('website-typecheck', ['node', 'website/node_modules/typescript/bin/tsc', '--noEmit', '--project', 'website/tsconfig.json']),
        ('website-structure', [sys.executable, 'scripts/check_website.py']),
        ('source-patterns', [sys.executable, 'scripts/static_checks.py']),
    ]
    LOGS.mkdir(parents=True, exist_ok=True); rows = []
    for name, command in checks:
        log = LOGS / ('amazon-audit-python-tests.log' if name == 'python-tests' else f'amazon-check-{name}.log')
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        rows.append({'check': name, 'status': 'PASS' if result.returncode == 0 else 'FAIL', 'exitCode': result.returncode, 'command': [Path(command[0]).name, *command[1:]], 'log': log.relative_to(ROOT).as_posix()})
        print(f'{name}: {rows[-1]["status"]}', flush=True)
    report = {'executedAt': datetime.now(timezone.utc).isoformat(), 'status': 'PASS' if all(row['exitCode'] == 0 for row in rows) else 'FAIL', 'checks': rows, 'scope': 'Structural, type, editorial regression and narrow source-pattern checks; no native linguistic, live billing, device or independent security approval.'}
    (ROOT / 'deliverables/reports/amazon-local-checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if report['status'] == 'PASS' else 1

if __name__ == '__main__': sys.exit(main())
