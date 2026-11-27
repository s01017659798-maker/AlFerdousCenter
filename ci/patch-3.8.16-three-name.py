#!/usr/bin/env python3
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_ROOT"])
hp = root / "app/src/main/assets/index.html"
html = hp.read_text(encoding="utf-8")
old = "if(name.split(' ').filter(Boolean).length<4){alert('اكتب الاسم رباعيًّا قبل الحفظ');return}"
new = "if(name.split(' ').filter(Boolean).length<3){alert('اكتب الاسم ثلاثيًا على الأقل؛ الاسم الرباعي اختياري.');return}"
if old in html:
    html = html.replace(old, new, 1)
elif new not in html:
    raise SystemExit("Student full-name validation anchor not found")
html = html.replace('content="3.8.15"', 'content="3.8.16"')
hp.write_text(html, encoding="utf-8")

gp = root / "app/build.gradle"
gradle = gp.read_text(encoding="utf-8")
gradle = re.sub(r"versionCode\s+\d+", "versionCode 397", gradle)
gradle = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '3.8.16'", gradle)
gp.write_text(gradle, encoding="utf-8")

readme = root / "README-AR.txt"
if readme.exists():
    text = readme.read_text(encoding="utf-8")
    text = text.replace("3.8.15", "3.8.16")
    text += "\n\nإصلاح 3.8.16: أصبح الاسم الثلاثي مقبولًا عند تسجيل الطالب، والاسم الرباعي اختياري.\n"
    readme.write_text(text, encoding="utf-8")

for p in (root / "tests").glob("*.test.cjs"):
    t = p.read_text(encoding="utf-8")
    t = t.replace("3.8.15", "3.8.16").replace(r"3\.8\.15", r"3\.8\.16")
    t = t.replace("versionCode 396", "versionCode 397")
    p.write_text(t, encoding="utf-8")

test = root / "tests/identity-validation.test.cjs"
test.write_text(r'''const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'app/src/main/assets/index.html'), 'utf8');
const gradle = fs.readFileSync(path.join(root, 'app/build.gradle'), 'utf8');

test('student names require at least three parts; four parts are optional', () => {
  assert.match(html, /name\.split\(' '\)\.filter\(Boolean\)\.length<3/);
  assert.match(html, /الاسم الرباعي اختياري/);
  assert.doesNotMatch(html, /name\.split\(' '\)\.filter\(Boolean\)\.length<4/);
});

test('release metadata is bumped for the student-name correction', () => {
  assert.match(gradle, /versionCode 397/);
  assert.match(gradle, /versionName '3\.8\.16'/);
});
''', encoding="utf-8")
print("Applied 3.8.16 three-name validation fix and regression test")
