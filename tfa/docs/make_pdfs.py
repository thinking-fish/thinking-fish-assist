#!/usr/bin/env python3
"""Render the Thinking Fish Assist markdown docs to branded A4 PDFs.

    python3 tfa/docs/make_pdfs.py <out-dir>

Needs the `markdown` package and a Chrome/Chromium (CHROME env var, or
chromium on PATH). Fonts: Geist if installed (as on thinking.fish), else system sans.
"""
import base64
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOCS = {
    "STAFF-GUIDE.md": "Thinking-Fish-Assist-Staff-Guide.pdf",
    "ANYDESK-REPLACEMENT.md": "Thinking-Fish-Assist-AnyDesk-Replacement.pdf",
    "SERVER.md": "Thinking-Fish-Assist-Server-Runbook.pdf",
}
CSS = """
@page { size: A4; margin: 16mm 15mm 18mm; }
body { font-family: Geist, 'Segoe UI', Arial, sans-serif; color: #1c1c22; font-size: 10.5pt; line-height: 1.55; }
header { display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #F26922; padding-bottom: 10px; margin-bottom: 14px; }
header img { width: 40px; height: 40px; }
header .t { font-weight: 600; font-size: 12pt; } header .s { color: #777; font-size: 9pt; }
h1 { font-size: 20pt; letter-spacing: -0.02em; margin: 6px 0 10px; }
h2 { font-size: 13.5pt; margin: 20px 0 6px; color: #16161a; border-bottom: 1px solid #e3e3e8; padding-bottom: 3px; break-after: avoid; }
h3 { font-size: 11.5pt; margin: 14px 0 4px; color: #F26922; break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9pt; break-inside: auto; }
th, td { border: 1px solid #dcdce2; padding: 5px 7px; text-align: left; vertical-align: top; }
th { background: #f4f4f6; }
tr { break-inside: avoid; }
code { font-family: 'Geist Mono', Menlo, Consolas, monospace; font-size: 8.8pt; background: #f4f4f6; padding: 1px 4px; border-radius: 3px; }
pre { background: #16161a; color: #f4f4f5; padding: 10px 12px; border-radius: 6px; white-space: pre-wrap; break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
a { color: #c24d10; text-decoration: none; }
footer { margin-top: 24px; color: #888; font-size: 8pt; border-top: 1px solid #e3e3e8; padding-top: 6px; }
"""


def chrome():
    return os.environ.get("CHROME") or "chromium"


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    icon = base64.b64encode(subprocess.check_output(
        ["rsvg-convert", "-w", "96", str(ROOT / "tfa/brand/icon.svg")])).decode()
    for src, pdf in DOCS.items():
        body = markdown.markdown((HERE / src).read_text(), extensions=["tables", "fenced_code"])
        html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<header><img src="data:image/png;base64,{icon}"><div><div class="t">Thinking Fish Assist</div>
<div class="s">Thinking Fish Ltd · internal</div></div></header>
{body}
<footer>Thinking Fish Ltd · thinking.fish · Source: github.com/thinking-fish/thinking-fish-assist/tree/thinking-fish/tfa/docs/{src}</footer>
</body></html>"""
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(html)
        subprocess.run([chrome(), "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out / pdf}", f"file://{f.name}"], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.unlink(f.name)
        print("wrote", out / pdf)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
