import tkinter
from pathlib import Path

version = Path('VERSION').read_text(encoding='utf-8').strip()
embedded_tcl = tkinter.Tcl().eval('info library').startswith('//zipfs:')
a = Analysis(['sleep_timer_gui.py'], pathex=[], binaries=[], datas=[('VERSION', '.')],
             hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=[], noarchive=False, optimize=0)
# Tcl/Tk 9 DLLs contain their own zipfs libraries; the standard hook wrongly
# requires external resource directories. Keep that hook for older installations.
if embedded_tcl:
    a.scripts = [item for item in a.scripts if item[0] != 'pyi_rth__tkinter']
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
          name='SleepTimer_' + version, debug=False,
          bootloader_ignore_signals=False, strip=False, upx=True,
          upx_exclude=[], runtime_tmpdir=None, console=False,
          disable_windowed_traceback=False, icon=['feather.ico'])
