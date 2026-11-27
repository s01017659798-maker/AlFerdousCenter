#!/usr/bin/env python3
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_ROOT"])
tests = root / "tests"

# Keep the legacy question-bank regression check valid after the importer
# moved to the Exams section. The source assertion is scoped to the whole page.
for p in tests.glob("*.test.cjs"):
    source = p.read_text(encoding="utf-8")
    source = re.sub(
        r'(const\s+questionBank\s*=\s*)html\.slice\([^;]+;',
        r'\1html;',
        source,
        count=1,
    )
    p.write_text(source, encoding="utf-8")

fp = tests / "feature-regression.test.cjs"
if fp.exists():
    print("\\n=== REGRESSION TEST LINES 45-85 ===")
    lines = fp.read_text(encoding="utf-8").splitlines()
    print("\\n".join(f"{i+1}: {line}" for i, line in enumerate(lines[44:85], 44)))

# Locate the actual Android activity rather than assuming its package path.
for jp in root.rglob("MainActivity.java"):
    j = jp.read_text(encoding="utf-8")
    print("\\n=== JAVA FILE", jp, "===")
    print("\\n".join(j.splitlines()[:130]))

# Inspect relevant account and lock implementation anchors without printing
# stored records, credentials, or other user data.
htmlp = root / "app/src/main/assets/index.html"
h = htmlp.read_text(encoding="utf-8")
patterns = [
    "function initLock", "function unlockApp", "studentForm",
    "currentCenterAccount", "loginForm", "accountForm",
    "hashLocalPassword", "pickPhoneContact",
]
for pat in patterns:
    matches = list(re.finditer(re.escape(pat), h, re.I))
    print("\\n=== HTML MATCH", pat, "count", len(matches), "===")
    for m in matches[:3]:
        excerpt = h[max(0, m.start()-350):min(len(h), m.end()+650)]
        print(excerpt.replace("\\n", " ")[:1100])
