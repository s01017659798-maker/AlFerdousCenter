#!/usr/bin/env python3
from pathlib import Path
import re, os, sys
root=Path(os.environ["PROJECT_ROOT"])
html_path=root/"app/src/main/assets/index.html"
s=html_path.read_text(encoding="utf-8")
s=s.replace('<meta name="app-version" content="3.8.9">','<meta name="app-version" content="3.8.10">')
old=re.search(r"function normalizeLoadedDatabase\(\)\{.*?\n\}",s,re.S)
if not old:
    raise SystemExit("normalizeLoadedDatabase function not found; refusing unsafe patch")
new="""function normalizeLoadedDatabase(){
 // تهيئة متزامنة كاملة قبل أول render؛ لا نعتمد على اكتمال IndexedDB لاحقًا.
 db.subjects ||= [{id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()}];
 if(!db.subjects.some(x=>x.id==='social-studies'))db.subjects.unshift({id:'social-studies',name:'الدراسات الاجتماعية',teacher:'',active:true,createdAt:new Date().toISOString()});
 db.groups ||= [];db.students ||= [];db.payments ||= [];db.attendance ||= [];
 db.classWhatsAppGroups ||= {};db.assessments ||= [];db.memos ||= [];db.exams ||= [];
 db.examAttempts ||= [];db.teachers ||= [];db.expenses ||= [];db.auditLog ||= [];
 db.lessonAssessments ||= [];db.lessonReminders ||= [];db.centerReminders ||= [];
 db.homework ||= [];db.homeworkSubmissions ||= [];db.questions ||= [];db.interactionRecords ||= [];
 db.accounts ||= {};db.settings ||= {};
 db.groups.forEach(g=>{if(!g.subjectId)g.subjectId='social-studies';if(g.active===undefined)g.active=true;if(!g.teacher)g.teacher=''});
 db.students.forEach(st=>{if(!st.subjectId){let g=db.groups.find(x=>x.id==st.groupId);st.subjectId=g?.subjectId||'social-studies'}if(!st.studentCode)st.studentCode=nextStudentCode()});
}"""
s=s[:old.start()]+new+s[old.end():]
anchor="tab('home');\nrender();\nupdateServerStatus();"
if anchor not in s:
    raise SystemExit("initial render anchor not found; refusing unsafe patch")
if "normalizeLoadedDatabase();\n"+anchor not in s:
    s=s.replace(anchor,"// إصلاح 3.8.10: تجهيز كل القوائم قبل أول عرض وربط للأزرار.\nnormalizeLoadedDatabase();\n"+anchor,1)
html_path.write_text(s,encoding="utf-8")
gradle=root/"app/build.gradle"
g=gradle.read_text(encoding="utf-8")
g=re.sub(r"versionCode\\s+\\d+","versionCode 390",g)
g=re.sub(r"versionName\\s+['\"][^'\"]+['\"]","versionName '3.8.10'",g)
gradle.write_text(g,encoding="utf-8")
print("Applied deterministic 3.8.10 initialization patch")
