"""Configure pinned PyPI CMake/Ninja in the ignored Android local.properties file."""
import os
from pathlib import Path
import shutil
import cmake
import ninja

root = Path(__file__).resolve().parents[1]
sdk = Path(os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT') or Path.home() / 'AppData/Local/Android/Sdk')
assert sdk.is_dir(), 'Configure ANDROID_HOME before native Android builds'
binary = 'ninja.exe' if os.name == 'nt' else 'ninja'
tools = Path(cmake.CMAKE_BIN_DIR)
shutil.copyfile(Path(ninja.BIN_DIR) / binary, tools / binary)
if os.name != 'nt': (tools / binary).chmod(0o755)
local = root / 'android/local.properties'
lines = local.read_text().splitlines() if local.exists() else []
lines = [line for line in lines if not line.startswith(('sdk.dir=', 'cmake.dir='))]
lines += ['sdk.dir=' + sdk.as_posix(), 'cmake.dir=' + tools.parent.as_posix()]
local.write_text('\n'.join(lines) + '\n')
print('Configured local Android SDK, CMake and Ninja paths')
