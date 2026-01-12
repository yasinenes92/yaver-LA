import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent

FILES = {
    "src_main": ROOT / "js" / "main.js",
    "dist_main": ROOT / "dist" / "js" / "main.js",
    "dist_min": ROOT / "dist" / "js" / "main.min.js",
}

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="utf-8", errors="replace")

def mtime(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    ts = p.stat().st_mtime
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def has(p: Path, pattern: str) -> bool:
    if not p.exists():
        return False
    s = read_text(p)
    return re.search(pattern, s) is not None

def count(p: Path, pattern: str) -> int:
    if not p.exists():
        return 0
    s = read_text(p)
    return len(re.findall(pattern, s))

def find_snippet(p: Path, pattern: str, ctx: int = 120) -> str:
    if not p.exists():
        return ""
    s = read_text(p)
    m = re.search(pattern, s)
    if not m:
        return ""
    a = max(0, m.start() - ctx)
    b = min(len(s), m.end() + ctx)
    return s[a:b].replace("\n", "\\n")

def main():
    print("== Yaver LA Diagnose ==")
    print("Project root:", ROOT)
    print()

    for k, p in FILES.items():
        print(f"[{k}] {p}")
        print("  exists:", p.exists())
        print("  mtime :", mtime(p))
        print()

    src = FILES["src_main"]
    dist_min = FILES["dist_min"]

    print("== Core checks ==")
    print("1) Marker in src_main:", has(src, r'__YAVER_LA_PATCH__\s*=\s*"v2-check-001"'))
    print("2) Marker in dist_min :", has(dist_min, r'__YAVER_LA_PATCH__\s*=\s*"v2-check-001"'))
    print()

    # The Apply button HTML uses inline onclick="applySettings()"
    inline_apply = count(dist_min, r'onclick=\'applySettings\(\)\'') + count(dist_min, r'onclick="applySettings\(\)"')
    print("3) Inline onclick applySettings() occurrences in dist_min:", inline_apply)

    # If inline apply exists, we MUST export window.applySettings
    export_apply = (
        has(dist_min, r'\.applySettings=') or
        has(dist_min, r'applySettings\s*=')
    )
    # better: specifically property assignment
    export_apply_specific = has(dist_min, r'(window|vt)\.applySettings\s*=')
    print("4) Looks like applySettings exported to window in dist_min:", export_apply_specific)
    if not export_apply_specific:
        print("   -> This is why you get: applySettings is not defined")
    print()

    # WB wombat wrapper detection
    wombat = has(src, r'WB\$wombat|_wb_wombat')
    print("5) Wayback (WB$wombat) wrapper detected in src_main:", wombat)
    if wombat:
        print("   -> Not fatal if you export functions to window, but it hides functions from global scope.")
    print()

    # encoding / mojibake detection
    mojibake = count(dist_min, r'Ã¢â€|ÃŽ|Ã˜Â|EspaÃƒ')
    print("6) Mojibake (broken-encoding) tokens found in dist_min:", mojibake)
    if mojibake:
        print("   snippet:", find_snippet(dist_min, r'Ã¢â€|ÃŽ|Ã˜Â|EspaÃƒ', 80))
    print()

    # multi-village helpers presence
    mv = has(src, r'function\s+mv_parseCoordFromRow') and has(src, r'function\s+mv_candidateSources')
    print("7) Multi-village helper functions present in src_main:", mv)
    print()

    print("== Recommended fix (if applySettings not exported) ==")
    if inline_apply and not export_apply_specific:
        print("Add this near the END of js/main.js (after functions are defined), then build + deploy:\n")
        print(r'''try {
  window.applySettings = applySettings;
  window.top.applySettings = applySettings;
  window.resetTable = resetTable;
  window.top.resetTable = resetTable;
  window.changeProfile = changeProfile;
  window.top.changeProfile = changeProfile;
  window.loadLanguage = loadLanguage;
  window.top.loadLanguage = loadLanguage;
  window.uglyHider = uglyHider;
  window.top.uglyHider = uglyHider;
  window.setKeyEditMode = setKeyEditMode;
  window.top.setKeyEditMode = setKeyEditMode;
} catch(e) { console.log("[Yaver] export failed", e); }''')
        print("\nThen run:\n  npm run build\n  npx gh-pages -d dist")
        print("\nAfter that, open your published main.min.js and search for 'window.applySettings'.")
    else:
        print("No export issue detected, or inline Apply not found. If game still errors, likely caching or other script overwriting handlers.")

if __name__ == "__main__":
    main()
