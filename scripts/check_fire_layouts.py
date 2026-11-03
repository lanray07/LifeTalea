"""Dedicated .debug QA smoke: rotation, 1.3x font and Wi-Fi-disabled reopen.

Restores original device settings in finally. Never targets the production package,
clears app data, or records audio. Run after instrumentation has completed onboarding.
"""
from pathlib import Path
import hashlib, io, json, os, subprocess, time
import xml.etree.ElementTree as ET
from PIL import Image
from fire_qa_session import awake_device

ROOT = Path(__file__).resolve().parents[1]
SDK = Path(os.environ.get('ANDROID_HOME', str(Path.home() / 'AppData/Local/Android/Sdk')))
ADB = SDK / 'platform-tools/adb.exe'
OUT = ROOT / 'deliverables/reports/device-evidence/layout-smoke'
PACKAGE = 'com.lifetalea.app.debug'

def adb(*args, binary=False):
    result = subprocess.run([str(ADB), *args], capture_output=True, timeout=40)
    if result.returncode: raise RuntimeError(f'ADB operation failed: {args[:3]}')
    return result.stdout if binary else result.stdout.decode('utf-8', errors='replace').strip()

def setting(key, value=None, table='system'):
    return adb('shell', 'settings', 'get', table, key) if value is None else adb('shell', 'settings', 'put', table, key, str(value))

def ensure_unlocked():
    adb('shell', 'input', 'keyevent', 'KEYCODE_WAKEUP')
    # Android only dismisses a non-secure keyguard; this cannot unlock a PIN/password.
    adb('shell', 'wm', 'dismiss-keyguard')
    if 'isStatusBarKeyguard=true' in adb('shell', 'dumpsys', 'window', 'policy'):
        raise RuntimeError('QA tablet is locked. Unlock it on the device; never put its PIN in a script or chat.')

def launch():
    ensure_unlocked()
    adb('shell', 'am', 'force-stop', PACKAGE)
    adb('shell', 'am', 'start', '-W', '-n', f'{PACKAGE}/com.lifetalea.app.MainActivity')

def capture(name):
    for _ in range(3):
        adb('shell', 'rm', '-f', '/sdcard/lifetalea-qa-layout.xml')
        try:
            adb('shell', 'uiautomator', 'dump', '/sdcard/lifetalea-qa-layout.xml')
            xml = adb('shell', 'cat', '/sdcard/lifetalea-qa-layout.xml')
            tree = ET.fromstring(xml)
        except (RuntimeError, ET.ParseError):
            time.sleep(1); continue
        if any(node.get('package') == PACKAGE and node.get('text') == 'Add a memory' for node in tree.iter('node')):
            break
        time.sleep(1)
    else: raise AssertionError(f'{name}: home action not available in accessibility tree')
    data = adb('exec-out', 'screencap', '-p', binary=True)
    with Image.open(io.BytesIO(data)) as image:
        width, height = image.size
    (OUT / f'{name}.png').write_bytes(data)
    (OUT / f'{name}.xml').write_text(xml, encoding='utf-8')
    nodes = [n for n in tree.iter('node') if n.get('package') == PACKAGE and n.get('text') == 'Add a memory']
    import re
    for node in nodes:
        left, top, right, bottom = map(int, re.findall(r'\d+', node.get('bounds', '')))
        assert 0 <= left < right <= width and 0 <= top < bottom <= height, f'{name}: home action outside display'
    return {'case': name, 'width': width, 'height': height, 'homeActionInAccessibilityTreeAndWithinDisplay': True}

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'result.json').write_text('{"status":"RUNNING"}\n', encoding='utf-8')
    apk_sha = hashlib.sha256((ROOT / 'android/app/build/outputs/apk/debug/app-debug.apk').read_bytes()).hexdigest()
    original = {key: setting(key) for key in ['accelerometer_rotation', 'user_rotation', 'font_scale']}
    wifi = setting('wifi_on', table='global')
    assert wifi in {'0', '1'}, 'Cannot safely restore an unknown Wi-Fi state'
    rows = []; restored = False; completed = False; failure = None
    try:
        ensure_unlocked()
        setting('accelerometer_rotation', 0); setting('font_scale', '1.3')
        for rotation in [0, 1]:
            setting('user_rotation', rotation); launch()
            rows.append(capture(f'rotation-{rotation}-font-1.3'))
        assert {r['width'] > r['height'] for r in rows} == {False, True}, 'Both orientations were not exercised'
        adb('shell', 'svc', 'wifi', 'disable')
        assert setting('wifi_on', table='global') == '0'
        launch(); rows.append(capture('wifi-disabled-reopen'))
        completed = True
    except Exception as error:
        failure = f'{type(error).__name__}: {error}'
        raise
    finally:
        adb('shell', 'svc', 'wifi', 'enable' if wifi == '1' else 'disable')
        for key, value in original.items():
            if value == 'null': adb('shell', 'settings', 'delete', 'system', key)
            else: setting(key, value)
        assert all(setting(key) == value for key, value in original.items())
        assert setting('wifi_on', table='global') == wifi
        restored = True
        adb('shell', 'rm', '-f', '/sdcard/lifetalea-qa-layout.xml')
        (OUT / 'result.json').write_text(json.dumps({'status': 'PASS' if completed else 'INCOMPLETE', 'debugApkSha256': apk_sha, 'originalSettingsRestored': restored, 'originalSettings': original, 'originalWifiState': wifi, 'failure': failure, 'cases': rows, 'scope': 'Home action accessibility bounds and launch only; manual screenshot inspection separate. Wi-Fi disabled does not certify prolonged offline use, every screen, all font scales or assistive technology.'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'cases': len(rows), 'originalSettingsRestored': restored}))

if __name__ == '__main__':
    qa_power={}
    try:
        with awake_device(ADB) as qa_power:
            main()
    finally:
        if qa_power and (OUT/'result.json').exists():
            report=json.loads((OUT/'result.json').read_text(encoding='utf-8'));report['qaPowerSettings']=qa_power
            (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
