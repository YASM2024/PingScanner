# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

src_path = "src"

common_hiddenimports = [
    "config",
    "database",
    "logger",
    "models",
    "run_lock",
    "scan_control",
    "scanner",
    "rate_limiter",
    "network_utils",
    "db_resolver",
]


def make_exe(
    script,
    name,
    console=True,
    hiddenimports=None,
    icon="icon.ico",
):

    analysis = Analysis(
        [script],
        pathex=[src_path],
        binaries=[],
        datas=[],
        hiddenimports=hiddenimports or [],
        hookspath=[],
        hooksconfig={},
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )

    pyz = PYZ(
        analysis.pure,
        analysis.zipped_data,
        cipher=block_cipher,
    )

    return EXE(
        pyz,
        analysis.scripts,
        analysis.binaries,
        analysis.zipfiles,
        analysis.datas,
        [],
        name=name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=console,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon,
    )


main_exe = make_exe(
    "src/main.py",
    "main",
    console=True,
    hiddenimports=common_hiddenimports,
)

export_csv_exe = make_exe(
    "src/export_csv.py",
    "export_csv",
    console=True,
    hiddenimports=["config", "network_utils", "db_resolver"],
)

remark_ui_exe = make_exe(
    "src/remark_ui.py",
    "remark_ui",
    console=False,
    hiddenimports=[
        "config",
        "database",
        "models",
        "network_utils",
        "db_resolver",
    ],
)
