#!/usr/bin/env python3
from pathlib import Path
import re, os

root = Path(os.environ["PROJECT_ROOT"])
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
s = s.replace('<meta name="app-version" content="3.8.9">', '<meta name="app-version" content="3.8.10">')

# Match only the original one-line function, never adjacent application code.
pattern = r"function normalizeLoadedDatabase\(\)\{[^\r\n]*\}"
old = re.search(pattern, s)
if not old:
    raise SystemExit("Could not locate the one-line database normalizer; refusing unsafe patch")
new = """function normalizeLoadedDatabase(){
 // تهيئة متزامنة كاملة قبل أول render؛ لا نعتمد على اكتمال IndexedDB لاحقًا.
 db.subjects ||= [{id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()}];
 if(!db.subjects.some(x=>x.id==='social-studies'))db.subjects.unshift({id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()});
 db.groups ||= [];db.students ||= [];db.payments ||= [];db.attendance ||= [];
 db.classWhatsAppGroups ||= {};db.assessments ||= [];db.memos ||= [];db.exams ||= [];
 db.examAttempts ||= [];db.teachers ||= [];db.expenses ||= [];db.auditLog ||= [];
 db.lessonAssessments ||= [];db.lessonReminders ||= [];db.centerReminders ||= [];
 db.homework ||= [];db.homeworkSubmissions ||= [];db.questions ||= [];db.interactionRecords ||= [];
 db.accounts ||= [];db.settings ||= {};
 db.groups.forEach(g=>{if(!g.subjectId)g.subjectId='social-studies';if(g.active===undefined)g.active=true;if(!g.teacher)g.teacher=''});
 db.students.forEach(st=>{if(!st.subjectId){let g=db.groups.find(x=>x.id==st.groupId);st.subjectId=g?.subjectId||'social-studies'}if(!st.studentCode)st.studentCode=nextStudentCode()});
}"""
s = s[:old.start()] + new + s[old.end():]

# Place the normalizer before the first startup render.
anchor = "tab('home');\nrender();\nupdateServerStatus();\ninitLock();"
if anchor not in s:
    raise SystemExit("Initial startup render block not found; refusing unsafe patch")
if "normalizeLoadedDatabase();\n" + anchor not in s:
    s = s.replace(anchor, "normalizeLoadedDatabase();\n" + anchor, 1)
html_path.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle"
g = gradle.read_text(encoding="utf-8")
g = re.sub(r"versionCode\s+\d+", "versionCode 390", g)
g = re.sub(r"versionName\s+.*", "versionName '3.8.10'", g)
gradle.write_text(g, encoding="utf-8")
# Keep regression expectations aligned with the repaired app version and guard the startup order.
for test_name in ("feature-regression.test.cjs", "security-hardening.test.cjs"):
    test_path = root / "tests" / test_name
    t = test_path.read_text(encoding="utf-8")
    t = t.replace("3.8.9", "3.8.10").replace("versionCode 389", "versionCode 390").replace(r"3\.8\.9", r"3\.8\.10")
    test_path.write_text(t, encoding="utf-8")

feature_test = root / "tests/feature-regression.test.cjs"
t = feature_test.read_text(encoding="utf-8")
if "fresh install normalizes database before the first render" not in t:
    t += """
\ntest('fresh install normalizes database before the first render', () => {
  assert.match(html, /normalizeLoadedDatabase\\(\\);\\s*tab\\('home'\\);\\s*render\\(\\);\\s*updateServerStatus\\(\\);\\s*initLock\\(\\);/);
});
"""
    feature_test.write_text(t, encoding="utf-8")

print("Applied 3.8.10 repair before first render")
