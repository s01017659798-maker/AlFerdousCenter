#!/usr/bin/env python3
from pathlib import Path
import re, os

root = Path(os.environ["PROJECT_ROOT"])
html_path = root / "app/src/main/assets/index.html"
s = html_path.read_text(encoding="utf-8")
s = s.replace('<meta name="app-version" content="3.8.9">', '<meta name="app-version" content="3.8.11">')
s = s.replace('<meta name="app-version" content="3.8.10">', '<meta name="app-version" content="3.8.11">')

pattern = r"function normalizeLoadedDatabase\(\)\{[^\r\n]*\}"
old = re.search(pattern, s)
if not old:
    raise SystemExit("Could not locate the one-line database normalizer; refusing unsafe patch")
new = """function normalizeLoadedDatabase(){
 db.subjects ||= [{id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()}];
 if(!db.subjects.some(x=>x.id==='social-studies'))db.subjects.unshift({id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()});
 db.groups ||= [];db.students ||= [];db.payments ||= [];db.attendance ||= [];
 db.classWhatsAppGroups ||= {};db.assessments ||= [];db.memos ||= [];db.exams ||= [];
 db.examAttempts ||= [];db.teachers ||= [];db.expenses ||= [];db.auditLog ||= [];
 db.lessonAssessments ||= [];db.lessonReminders ||= [];db.centerReminders ||= [];
 db.homework ||= [];db.homeworkSubmissions ||= [];db.questions ||= [];db.interactionRecords ||= [];
 db.accounts ||= [];db.settings ||= {};db.teacherPayments ||= [];
 db.groups.forEach(g=>{if(!g.subjectId)g.subjectId='social-studies';if(g.active===undefined)g.active=true;if(!g.teacher)g.teacher=''});
 db.students.forEach(st=>{if(!st.subjectId){let g=db.groups.find(x=>x.id==st.groupId);st.subjectId=g?.subjectId||'social-studies'}if(!st.studentCode)st.studentCode=nextStudentCode()});
}"""
s = s[:old.start()] + new + s[old.end():]

late = "let currentCenterAccount=null; // null = جلسة المدير بعد فتح قفل التطبيق"
if late not in s:
    late = "let currentCenterAccount=null;"
if late not in s:
    raise SystemExit("Could not locate the late currentCenterAccount declaration")
s = s.replace(late, "// currentCenterAccount is initialized near database bootstrap.", 1)
anchor_decl = "let currentStudentId=null;"
if anchor_decl not in s:
    raise SystemExit("Could not locate currentStudentId declaration")
if "let currentCenterAccount=null;" not in s:
    s = s.replace(anchor_decl, anchor_decl + "\n// إصلاح 3.8.11: تعريف جلسة الحساب قبل أي render أو فحص صلاحيات.\nlet currentCenterAccount=null;", 1)

anchor = "tab('home');\nrender();\nupdateServerStatus();\ninitLock();"
if anchor not in s:
    raise SystemExit("Initial startup render block not found")
if "normalizeLoadedDatabase();\n" + anchor not in s:
    s = s.replace(anchor, "normalizeLoadedDatabase();\n" + anchor, 1)
html_path.write_text(s, encoding="utf-8")

gradle = root / "app/build.gradle"
g = gradle.read_text(encoding="utf-8")
g = re.sub(r"versionCode\s+\d+", "versionCode 391", g)
g = re.sub(r"versionName\s+.*", "versionName '3.8.11'", g)
gradle.write_text(g, encoding="utf-8")

for test_name in ("feature-regression.test.cjs", "security-hardening.test.cjs"):
    test_path = root / "tests" / test_name
    t = test_path.read_text(encoding="utf-8")
    t = t.replace("3.8.9", "3.8.11").replace("3.8.10", "3.8.11")
    t = t.replace("versionCode 389", "versionCode 391").replace("versionCode 390", "versionCode 391")
    t = t.replace(r"3\.8\.9", r"3\.8\.11").replace(r"3\.8\.10", r"3\.8\.11")
    test_path.write_text(t, encoding="utf-8")

feature_test = root / "tests/feature-regression.test.cjs"
t = feature_test.read_text(encoding="utf-8")
if "account session binding exists before startup render paths" not in t:
    t += """
\ntest('account session binding exists before startup render paths', () => {
  const declaration = html.indexOf('let currentCenterAccount=null;');
  const earlyUse = html.indexOf('function renderStudentFilters');
  const firstStartupRender = html.indexOf("tab('home');\\nrender();");
  assert.ok(declaration >= 0 && earlyUse > declaration && firstStartupRender > declaration);
  assert.equal((html.match(/let currentCenterAccount=null;/g) || []).length, 1);
});
"""
    feature_test.write_text(t, encoding="utf-8")

print("Applied 3.8.11 account-session startup repair")
