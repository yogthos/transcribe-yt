# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['transcribe_yt_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('transcribe_yt.py', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'gi',
        'gi.repository.Gtk',
        'gi.repository.Gdk',
        'gi.repository.GLib',
        'gi.repository.Pango',
        'markdown',
        'beautifulsoup4',
        'requests',
        'nemo.collections.asr',
        'transformers',
        'torch',
        'tokenizers',
        'sentencepiece',
        'protobuf',
        'onnx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude GStreamer and media libraries
        'gi.repository.Gst',
        'gi.repository.GstVideo',
        'gi.repository.GstAudio',
        'gi.repository.GstPbutils',
        'gstreamer',
        'gst',
        'Gst',
        'GstVideo',
        'GstAudio',
        'GstPbutils',
        # Exclude other unnecessary libraries
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tensorflow',
        'sklearn',
        'PIL',
        'cv2',
        'opencv',
        'ffmpeg',
        'libav',
        # Exclude web frameworks
        'flask',
        'django',
        'tornado',
        'fastapi',
        # Exclude database libraries
        'sqlite3',
        'psycopg2',
        'pymongo',
        'redis',
        # Exclude other GUI libraries
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        # Exclude Jupyter/IPython
        'IPython',
        'jupyter',
        'notebook',
        # Exclude testing frameworks
        'pytest',
        'unittest',
        'nose',
        # Exclude other unnecessary packages
        'setuptools',
        'distutils',
        'pip',
        'wheel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TranscribeYouTube',
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
    codesign_identity='-',  # Use ad-hoc signing
    entitlements_file=None,
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
)

app = BUNDLE(
    exe,
    name='TranscribeYouTube.app',
    icon='app_icon.icns' if os.path.exists('app_icon.icns') else None,
    bundle_identifier='com.transcribeyt.app',
    info_plist={
        'CFBundleName': 'Transcribe YouTube',
        'CFBundleDisplayName': 'Transcribe YouTube',
        'CFBundleVersion': '1.0',
        'CFBundleShortVersionString': '1.0',
        'CFBundleIdentifier': 'com.transcribeyt.app',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'YouTube URL',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.url'],
            }
        ],
    },
)
