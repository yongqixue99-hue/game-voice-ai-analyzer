# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the real LUNARIS backend sidecar.

Entry: desktop_entry.py -> uvicorn -> app.main:app.

Hidden imports / collected packages cover the dynamic-import blind spots the P3
readiness audit called out:
  - sqlalchemy.dialects.sqlite  (loaded by URL string, not statically imported)
  - uvicorn lifespan/protocol/loop impls (selected at runtime by name)
  - pydantic / pydantic_core      (compiled core + lazily imported submodules)
  - multipart (python-multipart)  (form parsing, imported by name)
  - the whole `app` package        (routers imported via include_router strings)
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
    "sqlalchemy.dialects.sqlite",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.http.httptools_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.loops.asyncio",
    "multipart",
    "python_multipart",
]
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("pydantic")
hiddenimports += collect_submodules("pydantic_core")

a = Analysis(
    ['desktop_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='lunaris-real-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
