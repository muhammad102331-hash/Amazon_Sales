"""
generate_pdf.py
───────────────
Converts amazon_sales_report.html → amazon_sales_report.pdf
using Chrome/Edge headless (no extra Python lib required).

Run:
    python generate_pdf.py
"""

import subprocess
import sys
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROJECT_ROOT = BASE.parent
HTML = PROJECT_ROOT / "reports" / "html" / "amazon_sales_report.html"
PDF = PROJECT_ROOT / "reports" / "pdf" / "amazon_sales_report.pdf"

# Common Chrome/Edge paths on Windows
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    shutil.which("google-chrome") or "",
    shutil.which("chromium-browser") or "",
    shutil.which("msedge") or "",
]

browser = next((b for b in BROWSERS if b and Path(b).exists()), None)

if not browser:
    print("❌  Chrome/Edge not found. Open amazon_sales_report.html in Chrome,")
    print("    press Ctrl+P, choose 'Save as PDF', set margins to None.")
    sys.exit(1)

if not HTML.exists():
    print(f"❌  HTML report not found: {HTML}")
    print("    Run src/analysis.py first to generate the HTML report.")
    sys.exit(1)

PDF.parent.mkdir(parents=True, exist_ok=True)

cmd = [
    browser,
    "--headless",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    f"--print-to-pdf={PDF}",
    "--print-to-pdf-no-header",
    str(HTML.resolve()),
]

print(f"Using: {browser}")
print("Generating PDF … (may take 15-30 s)")
result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

if PDF.exists():
    print(f"✅  PDF saved → {PDF}  ({PDF.stat().st_size / 1024:.0f} KB)")
else:
    print("❌  PDF generation failed.")
    print(result.stderr)
