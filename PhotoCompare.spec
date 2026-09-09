# -*- mode: python ; coding: utf-8 -*-

# Definimos as variáveis de identificação do projeto aqui
NOME_PROJETO = "PhotoCompare"
VERSAO_PROJETO = "1.0.2"

# Combinamos o nome e a versão para formar o nome final do executável
NOME_EXECUTAVEL = f"{NOME_PROJETO}_v{VERSAO_PROJETO}"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['tkinterdnd2'],
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
    name=NOME_EXECUTAVEL,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.ico'],
)
