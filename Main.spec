# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['Main.py'],
             pathex=[],
             binaries=[],
             datas=[('best.pt', '.'), ('yolov5', 'yolov5')],
             hiddenimports=['numpy', 'tqdm', 'requests', 'PyYAML', 'scipy', 'Pillow', 'tensorboard', 'yaml', 'PIL', 'seaborn'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
for d in a.datas:
    if "_C.cp39-win_amd64.pyd" in d[0]:
        a.datas.remove(d)
        break
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='厨余垃圾异常检测系统Beta,V1.2',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
