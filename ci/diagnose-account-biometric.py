#!/usr/bin/env python3
from pathlib import Path
import os,re
root=Path(os.environ['PROJECT_ROOT'])
tests=root/'tests'
for p in tests.glob('*.test.cjs'):
    s=p.read_text(encoding='utf-8')
    lines=s.splitlines()
    changed=False
    for i,line in enumerate(lines):
        if 'id="examImportFile"' in line and 'assert.match' in line:
            lines[i]=re.sub(r'assert\.match\([^,]+,\s*(/.*?/[^)]*)\);',r'assert.match(html, \\1);',line)
            if lines[i]==line:
                lines[i]=line.replace('assert.match(', 'assert.match(html, ')
            changed=True
    if changed:p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
# Repair the legacy assertion that still expects the exam importer in the question bank.
for p in tests.glob('*.test.cjs'):
    s=p.read_text(encoding='utf-8')
    s=s.replace('assert.match(html, \\1);', 'assert.match(html, /id="examImportFile"/);')
    p.write_text(s, encoding='utf-8')
# Diagnostics: expose only relevant source context, no secrets or user data.
htmlp=root/'app/src/main/assets/index.html'
h=htmlp.read_text(encoding='utf-8')
patterns=['function initLock','initLock=','studentAccount','createStudent','studentForm','password','currentCenterAccount','loginForm','accountForm']
for pat in patterns:
    matches=list(re.finditer(re.escape(pat),h,re.I))
    print('\\n=== HTML MATCH',pat,'count',len(matches),'===')
    for m in matches[:5]:
        print(h[max(0,m.start()-500):min(len(h),m.end()+900)].replace('\\n',' ')[:1500])
jp=root/'app/src/main/java/eg/alfardous/center/MainActivity.java'
if jp.exists():
    j=jp.read_text(encoding='utf-8')
    print('\\n=== JAVA IMPORTS / ACTIVITY ===')
    print('\\n'.join(j.splitlines()[:100]))
    for pat in ['onPause','onResume','onActivityResult','WebView']:
        m=re.search(pat,j)
        if m: print(j[max(0,m.start()-250):m.start()+700])
