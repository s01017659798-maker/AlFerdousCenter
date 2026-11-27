#!/usr/bin/env python3
from pathlib import Path
import re, os
root=Path(os.environ["PROJECT_ROOT"])
hp=root/"app/src/main/assets/index.html"
s=hp.read_text(encoding="utf-8")
s=s.replace('content="3.8.9"','content="3.8.13"').replace('content="3.8.10"','content="3.8.12"').replace('content="3.8.11"','content="3.8.12"')
m=re.search(r"function normalizeLoadedDatabase\(\)\{[^\r\n]*\}",s)
if not m: raise SystemExit("Database normalizer not found")
normalizer="""function normalizeLoadedDatabase(){
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
s=s[:m.start()]+normalizer+s[m.end():]
late="let currentCenterAccount=null; // null = جلسة المدير بعد فتح قفل التطبيق"
if late not in s:late="let currentCenterAccount=null;"
if late in s:s=s.replace(late,"// currentCenterAccount is initialized near database bootstrap.",1)
if "let currentCenterAccount=null;" not in s:
 a="let currentStudentId=null;"
 if a not in s:raise SystemExit("Account declaration anchor missing")
 s=s.replace(a,a+"\n// 3.8.11 startup repair\nlet currentCenterAccount=null;",1)
anchor="tab('home');\nrender();\nupdateServerStatus();\ninitLock();"
if anchor not in s:raise SystemExit("Startup render anchor missing")
if "normalizeLoadedDatabase();\n"+anchor not in s:s=s.replace(anchor,"normalizeLoadedDatabase();\n"+anchor,1)
if '<h2>استيراد امتحان من ملف</h2>' not in s:raise SystemExit("Import panel missing")
if s.index('<h2>استيراد امتحان من ملف</h2>') < s.index('<section id="questionBank"'):
 start=s.index('  <div class="panel" style="border:2px solid var(--gold);margin-bottom:16px">\n   <h2>استيراد امتحان من ملف</h2>')
 end=s.index('\n  </div>\n  <form id="examForm">',start)+len('\n  </div>')
 panel=s[start:end];s=s[:start]+s[end:]
 hint='  <p class="hint">أضف الأسئلة مرة واحدة، ثم كوّن امتحانًا منها حسب المادة والصف والوحدة والدرس. كل امتحان يُحفظ بنسخة مستقلة من الأسئلة والإجابات.</p>\n'
 if hint not in s:raise SystemExit("Question bank panel anchor missing")
 s=s.replace(hint,hint+panel+'\n',1)
s=s.replace('<div id="importQuestionReview" class="hidden" style="margin-top:12px"></div>','<div id="examImportMediaPreview" class="panel" style="margin-top:10px"></div><div id="importQuestionReview" class="hidden" style="margin-top:12px"></div>',1)
old="  importedExamText=txt;$('examImportTitle').value=$('examImportTitle').value||f.name.replace(/\\.[^.]+$/,'');$('examImportText').value=txt;$('examImportPreview').classList.remove('hidden');"
new="  importedExamText=txt;$('examImportTitle').value=$('examImportTitle').value||f.name.replace(/\\.[^.]+$/,'');$('examImportText').value=txt;let mediaPreview=$('examImportMediaPreview');if(mediaPreview)mediaPreview.innerHTML=importedExamMedia.map((m,i)=>m.type==='image'?('<figure class=\"panel\" style=\"display:inline-block;max-width:180px;margin:5px\"><img src=\"'+m.data+'\" alt=\"'+esc(m.name)+'\" style=\"max-width:100%;max-height:160px;object-fit:contain\"><figcaption>'+esc(m.name||('صورة '+(i+1)))+'</figcaption></figure>'):'').join('');$('examImportPreview').classList.remove('hidden');"
if old not in s:raise SystemExit("Import preview insertion point missing")
s=s.replace(old,new,1)
old="questions,imported:true,createdAt:new Date().toISOString()};"
new="questions,imported:true,sourceMedia:importedExamMedia.slice(),sourceFileName:$('examImportFile')?.files?.[0]?.name||'',createdAt:new Date().toISOString()};"
if old not in s:raise SystemExit("Imported exam data model missing")
s=s.replace(old,new,1)
# Show source maps/images to students and preserve them in exported exam packages.
old_runner="$('runnerQuestions').innerHTML=order.map((q,i)=>"
new_runner="const sourceMediaHtml=(ex.sourceMedia||[]).filter(m=>m&&m.type==='image'&&m.data).map(m=>'<figure class=\\\"panel\\\" style=\\\"margin:8px 0;text-align:center\\\"><img src=\\\"'+m.data+'\\\" alt=\\\"'+esc(m.name||'مرفق الامتحان')+'\\\" style=\\\"max-width:100%;max-height:300px;object-fit:contain\\\"><figcaption>'+esc(m.name||'مرفق الامتحان')+'</figcaption></figure>').join('');$('runnerQuestions').innerHTML=(sourceMediaHtml?'<div class=\\\"panel\\\"><h3>صور وخرائط مرفقة بالامتحان</h3>'+sourceMediaHtml+'</div>':'')+order.map((q,i)=>"
if old_runner not in s:raise SystemExit("Exam runner render anchor missing")
s=s.replace(old_runner,new_runner,1)
if 'sourceMedia:ex.sourceMedia||[]' not in s:s=s.replace('questions:ex.questions}}','questions:ex.questions,sourceMedia:ex.sourceMedia||[]}}',1)
# Clear imported source media and preview together with imported text.
old_clear="function clearExamImport(){importedExamText='';$('examImportFile').value='';$('examImportText').value='';$('examImportPreview').classList.add('hidden');$('examImportStatus').textContent='';}"
new_clear="function clearExamImport(){importedExamText='';importedExamMedia=[];importedQuestionsDraft=[];importedDraftSaved=false;$('examImportFile').value='';$('examImportText').value='';$('examImportPreview').classList.add('hidden');$('examImportMediaPreview').innerHTML='';$('importQuestionReview').classList.add('hidden');$('examImportStatus').textContent='';}"
if old_clear not in s: raise SystemExit("Clear import function anchor missing")
s=s.replace(old_clear,new_clear,1)
hp.write_text(s,encoding="utf-8")
gp=root/"app/build.gradle";g=gp.read_text(encoding="utf-8")
g=re.sub(r"versionCode\s+\d+","versionCode 393",g);g=re.sub(r"versionName\s+.*","versionName '3.8.12'",g);gp.write_text(g,encoding="utf-8")
for name in ("feature-regression.test.cjs","security-hardening.test.cjs"):
 p=root/"tests"/name;t=p.read_text(encoding="utf-8")
 t=t.replace("3.8.9","3.8.12").replace("3.8.10","3.8.12").replace("3.8.11","3.8.12")
 t=t.replace(r"3\.8\.9",r"3\.8\.12").replace(r"3\.8\.10",r"3\.8\.12").replace(r"3\.8\.11",r"3\.8\.12")
 for v in (389,390,391):t=t.replace(f"versionCode {v}","versionCode 392")
 p.write_text(t,encoding="utf-8")
p=root/"tests/feature-regression.test.cjs";t=p.read_text(encoding="utf-8")
if "question bank includes source-file import" not in t:
 t+='''

test('question bank includes source-file import, preview, question review, and exam creation workflow', () => {
 const a=html.indexOf('<section id="questionBank"'), b=html.indexOf('</section>',a), bank=html.slice(a,b);
 assert.match(bank,/id="examImportFile"/);
 assert.match(bank,/accept="\\.docx,\\.pdf,\\.png,\\.jpg,\\.jpeg,\\.webp"/);
 assert.match(bank,/onclick="importExamDocument\\(\\)"/);
 assert.match(bank,/id="examImportText"/);
 assert.match(bank,/id="examImportMediaPreview"/);
 assert.match(bank,/onclick="prepareImportedExamDraft\\(\\)"/);
 assert.match(bank,/id="importQuestionReview"/);
 assert.match(html,/function saveImportedExamAsElectronic\\(\\)/);
 assert.match(html,/sourceMedia:importedExamMedia\\.slice\\(\\)/);
 assert.match(html,/كل سؤال يحتاج إجابة صحيحة محددة يدويًا/);
 assert.match(html,/const sourceMediaHtml=\\(ex\\.sourceMedia\\|\\|\\[\\]\\)/);
 assert.match(html,/sourceMedia:ex\\.sourceMedia\\|\\|\\[\\]/);
});
'''
 p.write_text(t,encoding="utf-8")
p=root/"tests/feature-regression.test.cjs";t=p.read_text(encoding="utf-8")
if "clearing imported exam source removes all attached media" not in t:
 t+='''

test('clearing imported exam source removes all attached media and draft review', () => {
 assert.match(html,/function clearExamImport\\(\\)\\{[^}]*importedExamMedia=\\[\\][^}]*importedQuestionsDraft=\\[\\][^}]*importedDraftSaved=false/);
 assert.match(html,/function clearExamImport\\(\\)\\{[^}]*examImportMediaPreview[^}]*innerHTML=''/);
 assert.match(html,/function clearExamImport\\(\\)\\{[^}]*importQuestionReview[^}]*classList\\.add\\('hidden'\\)/);
});
'''
p.write_text(t,encoding="utf-8")
print("Applied 3.8.13 import cleanup repair and regression test")
