#!/usr/bin/env python3
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_ROOT"])
hp = root / "app/src/main/assets/index.html"
html = hp.read_text(encoding="utf-8")

anchor = '  <p class="hint">أضف الأسئلة مرة واحدة، ثم كوّن امتحانًا منها حسب المادة والصف والوحدة والدرس. كل امتحان يُحفظ بنسخة مستقلة من الأسئلة والإجابات.</p>'
panel = anchor + """
  <div class="panel" style="margin:12px 0;border:2px solid var(--gold)">
   <h3>استيراد ملف إلى بنك الأسئلة</h3>
   <p class="hint">يمكنك بدء رفع Word أو PDF أو صورة من هنا. ستفتح أداة الاستيراد نفسها داخل قسم الامتحانات، وتعرض النص والصور لمراجعتها ثم تحويل الأسئلة إلى بنك الأسئلة وامتحان إلكتروني.</p>
   <button type="button" class="btn gold" onclick="openExamImportFromQuestionBank()">رفع ملف إلى بنك الأسئلة ومراجعته</button>
  </div>"""
if 'onclick="openExamImportFromQuestionBank()"' not in html:
    if anchor not in html:
        raise SystemExit("Question bank introduction anchor missing")
    html = html.replace(anchor, panel, 1)

if "window.openExamImportFromQuestionBank=function()" not in html:
    js = """
window.openExamImportFromQuestionBank=function(){
 tab('exams');
 const file=$('examImportFile');
 if(!file){alert('أداة استيراد الامتحانات غير متاحة حاليًا.');return;}
 file.addEventListener('change',function(){
  if(file.files&&file.files.length)importExamDocument();
 },{once:true});
 file.scrollIntoView({behavior:'smooth',block:'center'});
 file.click();
};
"""
    anchor_js = "function openWhatsApp(text,phone=''){"
    if anchor_js not in html:
        raise SystemExit("Question bank import entry JS anchor missing")
    html = html.replace(anchor_js, js + "\n" + anchor_js, 1)

html = html.replace('content="3.8.17"', 'content="3.8.18"')
hp.write_text(html, encoding="utf-8")

gp = root / "app/build.gradle"
gradle = gp.read_text(encoding="utf-8")
gradle = re.sub(r"versionCode\s+\d+", "versionCode 399", gradle)
gradle = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '3.8.18'", gradle)
gp.write_text(gradle, encoding="utf-8")

readme = root / "README-AR.txt"
if readme.exists():
    text = readme.read_text(encoding="utf-8").replace("3.8.17", "3.8.18")
    text += "\n\nإضافة 3.8.18: أصبح رفع ملفات Word وPDF والصور متاحًا من بنك الأسئلة أيضًا، مع استخدام أداة المعاينة والتحويل نفسها دون تكرار حقول الاستيراد.\n"
    readme.write_text(text, encoding="utf-8")

for p in (root / "tests").glob("*.test.cjs"):
    t = p.read_text(encoding="utf-8")
    t = t.replace("3.8.17", "3.8.18").replace(r"3\.8\.17", r"3\.8\.18")
    t = t.replace("versionCode 398", "versionCode 399")
    p.write_text(t, encoding="utf-8")

test = root / "tests/question-bank-import-entry.test.cjs"
test.write_text(r'''const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'app/src/main/assets/index.html'),'utf8');
const bank=html.slice(html.indexOf('<section id="questionBank"'),html.indexOf('</section>',html.indexOf('<section id="questionBank"')));
test('question bank provides direct access to the shared document import and review workflow',()=>{
 assert.match(bank,/onclick="openExamImportFromQuestionBank\(\)"/);
 assert.match(bank,/رفع ملف إلى بنك الأسئلة ومراجعته/);
 assert.match(html,/window\.openExamImportFromQuestionBank=function\(\)/);
 assert.match(html,/tab\('exams'\)/);
 assert.match(html,/file\.addEventListener\('change'/);
 assert.match(html,/importExamDocument\(\)/);
});
test('shared import remains available in the electronic exams section',()=>{
 const a=html.indexOf('<section id="exams"'),b=html.indexOf('<section id="questionBank"'),exams=html.slice(a,b);
 assert.match(exams,/id="examImportFile"/);
 assert.match(exams,/onclick="prepareImportedExamDraft\(\)"/);
});
''',encoding="utf-8")
print("Applied 3.8.18 question-bank import entry and regression tests")
