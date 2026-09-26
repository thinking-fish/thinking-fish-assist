#!/usr/bin/env python3
"""Thinking Fish Assist: finish branding the WiX (MSI) sources after preprocess.py.

Upstream's res/msi/preprocess.py already swaps "RustDesk" for --app-name
everywhere. Our --app-name is the internal, space-free "ThinkingFishAssist"
(it names the install folder, the .exe, the Windows service and registry keys,
all of which upstream assumes are alphanumeric). This script only changes the
strings a person READS in the installer and in Settings > Apps, to
"Thinking Fish Assist". It never touches identifiers, paths or shortcut names,
because the app's own uninstall code deletes shortcuts by the internal name.

Run from res/msi after preprocess.py:  python ../../tfa/msi_branding.py
"""
import re
from pathlib import Path

INTERNAL = "ThinkingFishAssist"
DISPLAY = "Thinking Fish Assist"
HERE = Path.cwd()


def sub(path: Path, pattern: str, repl: str, count_min: int = 1):
    s = path.read_text(encoding="utf-8")
    s2, n = re.subn(pattern, repl, s)
    if n < count_min:
        raise SystemExit(f"msi_branding: pattern not found in {path}: {pattern}")
    path.write_text(s2, encoding="utf-8")
    print(f"{path}: {n} replacement(s)")


# The MSI package name is what "Apps & features" shows for an MSI install.
sub(HERE / "Package/Package.wxs", r'<Package Name="\$\(var\.Product\)"', f'<Package Name="{DISPLAY}"')

# Add/Remove Programs DisplayName written by gen_custom_ARPSYSTEMCOMPONENT (--arp).
for p in (HERE / "Package").rglob("*.wxs"):
    s = p.read_text(encoding="utf-8")
    if f'Name="DisplayName" Value="{INTERNAL}"' in s:
        sub(p, f'Name="DisplayName" Value="{INTERNAL}"', f'Name="DisplayName" Value="{DISPLAY}"')

# Installer UI text: descriptions and comments only (never shortcut names).
for wxl in (HERE / "Package/Language").glob("*.wxl"):
    s = wxl.read_text(encoding="utf-8")
    out = []
    for line in s.splitlines(keepends=True):
        m = re.search(r'<String Id="([^"]+)"', line)
        if m and (m.group(1).endswith("_Desc") or m.group(1) == "AR_Comment" or "Welcome" in m.group(1)
                  or m.group(1).startswith(("Dlg", "Install", "Error", "Service_", "MyInstallDirDlg"))):
            line = line.replace(INTERNAL, DISPLAY)
        out.append(line)
    wxl.write_text("".join(out), encoding="utf-8")
    print(f"{wxl}: display strings updated")
