#!/usr/bin/env python3
from pathlib import Path
import os, re
root=Path(os.environ['PROJECT_ROOT'])
html_path=root/'app/src/main/assets/index.html'
html=html_path.read_text(encoding='utf-8')
def once(old,new,label,s):
    if old not in s: raise SystemExit('Missing patch anchor: '+label)
    return s.replace(old,new,1)
start=html.find('  <div class="panel" style="border:2px solid var(--gold);margin-bottom:16px">\n   <h2>استيراد امتحان من ملف</h2>')
if start<0: raise SystemExit('Exam file import panel not found')
end_marker='\n  <div class="panel" style="margin:12px 0">\n   <h3>إضافة سؤال إلى البنك</h3>'
end=html.find(end_marker,start)
if end<0: raise SystemExit('Question bank panel end marker not found')
import_panel=html[start:end]
html=html[:start]+html[end:]
exam_anchor='  <p class="hint">أنشئ الامتحان هنا ليحله الطالب من هاتفه عبر رابط مستقل في المتصفح. بعد تجهيز خادم الامتحانات ونشر الامتحان، ترسل للطلاب رابط البوابة وكود الامتحان وكود كل طالب. حاليًا يتم حفظ إعداد الامتحان على هذا الجهاز، ولم يتم إنشاء رابط عام أو ربط الخادم بعد.</p>'
html=once(exam_anchor,exam_anchor+'\n'+import_panel,'place file import panel inside exams',html)
memo_anchor='   <label>المحتوى</label><textarea id="memoContent" required placeholder="اكتب شرح الدرس أو الأسئلة أو نقاط المراجعة هنا..."></textarea>'
memo_upload='''   <div class="panel" style="margin:10px 0;border:1px dashed var(--gold)">
    <label>رفع مذكرة أو مراجعة من ملف (Word DOCX أو PDF أو صورة)</label>
    <input id="memoImportFile" type="file" accept=".docx,.pdf,.png,.jpg,.jpeg,.webp">
    <div class="actions"><button class="btn light" type="button" onclick="processMemoFile()">قراءة الملف وإدراج محتواه</button></div>
    <p id="memoImportStatus" class="hint" aria-live="polite">يمكنك رفع الملف بدل كتابة المحتوى يدويًا، ثم مراجعة النص وتعديله قبل الحفظ.</p>
    <div id="memoImportPreview" class="hint"></div>
   </div>
'''
html=once(memo_anchor,memo_upload+memo_anchor,'memo file upload control',html)
old="let editingMemoId=null;$('memoForm').onsubmit=e=>{e.preventDefault();let data={type:$('memoType').value,grade:$('memoGrade').value,title:$('memoTitle').value.trim(),unit:$('memoUnit').value.trim(),lesson:$('memoLesson').value.trim(),content:$('memoContent').value.trim(),date:today};if(editingMemoId!==null){let old=db.memos.find(x=>x.id===editingMemoId);if(old)Object.assign(old,data);editingMemoId=null}else db.memos.unshift({id:Date.now(),...data});e.target.reset();save();alert('تم حفظ المذكرة / المراجعة على هذا الجهاز')};"
new="""let editingMemoId=null;let memoUploadImages=[];
async function processMemoFile(){
 const file=$('memoImportFile')?.files?.[0];if(!file){alert('اختر ملف المذكرة أولًا');return;}
 const status=$('memoImportStatus');status.textContent='جارٍ قراءة الملف…';
 try{
  const transfer=new DataTransfer();transfer.items.add(file);$('examImportFile').files=transfer.files;
  $('examImportTitle').value=file.name.replace(/\\.[^.]+$/,'');$('examImportGrade').value=$('memoGrade').value;
  await importExamDocument();
  if($('examImportPreview').classList.contains('hidden'))throw new Error($('examImportStatus').textContent||'تعذرت قراءة الملف');
  const extracted=$('examImportText').value.trim();if(!extracted)throw new Error('لم يتم استخراج نص من الملف.');
  $('memoContent').value=extracted;$('memoTitle').value=$('memoTitle').value.trim()||$('examImportTitle').value;
  memoUploadImages=importedExamMedia.slice();
  $('memoImportPreview').textContent='تم تجهيز '+(memoUploadImages.length?memoUploadImages.length+' صورة/صفحة مرفقة':'النص المستخرج')+'. راجع المحتوى في خانة المذكرة قبل الحفظ.';
  status.textContent='تمت قراءة الملف بنجاح وإدراج النص في المذكرة.';
 }catch(err){memoUploadImages=[];status.textContent='تعذر قراءة الملف: '+(err.message||err);}
}
$('memoForm').onsubmit=e=>{e.preventDefault();let data={type:$('memoType').value,grade:$('memoGrade').value,title:$('memoTitle').value.trim(),unit:$('memoUnit').value.trim(),lesson:$('memoLesson').value.trim(),content:$('memoContent').value.trim(),images:memoUploadImages.length?memoUploadImages.slice():(editingMemoId!==null?(db.memos.find(x=>x.id===editingMemoId)?.images||[]):[]),date:today};if(editingMemoId!==null){let old=db.memos.find(x=>x.id===editingMemoId);if(old)Object.assign(old,data);editingMemoId=null}else db.memos.unshift({id:Date.now(),...data});e.target.reset();memoUploadImages=[];$('memoImportPreview').textContent='';$('memoImportStatus').textContent='يمكنك رفع ملف جديد أو كتابة المحتوى يدويًا.';save();renderMemos();alert('تم حفظ المذكرة / المراجعة على هذا الجهاز')};"""
html=once(old,new,'memo submit handler',html)
html=once("$('memoContent').value=m.content||'';$('memoForm').scrollIntoView", "$('memoContent').value=m.content||'';memoUploadImages=[];$('memoImportPreview').textContent=(m.images||[]).length?'المذكرة تحتوي على '+m.images.length+' مرفق محفوظ. ارفع ملفًا جديدًا لاستبدال المرفقات.':'';$('memoForm').scrollIntoView", 'memo edit attachment preservation',html)
html=html.replace('3.8.14','3.8.15')
html_path.write_text(html,encoding='utf-8')
gp=root/'app/build.gradle';g=gp.read_text(encoding='utf-8')
g=re.sub(r'versionCode\s+\d+','versionCode 396',g)
g=re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '3.8.15'", g)
gp.write_text(g,encoding='utf-8')
for p in (root/'tests').glob('*.test.cjs'):
    t=p.read_text(encoding='utf-8').replace('3.8.14','3.8.15').replace(r'3\.8\.14',r'3\.8\.15').replace('versionCode 395','versionCode 396')
    p.write_text(t,encoding='utf-8')
(root/'tests/file-import.test.cjs').write_text(r'''const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const html=fs.readFileSync(path.join(__dirname,'../app/src/main/assets/index.html'),'utf8');
const exams=html.slice(html.indexOf('<section id="exams"'),html.indexOf('<section id="questionBank"'));
const memos=html.slice(html.indexOf('<section id="memos"'),html.indexOf('<section id="exams"'));
test('memos allow DOCX PDF and image uploads and reuse the document reader',()=>{
 assert.match(memos,/id="memoImportFile"[^>]*accept="\.docx,\.pdf,\.png,\.jpg,\.jpeg,\.webp"/);
 assert.match(html,/async function processMemoFile\(\)/);
 assert.match(html,/await importExamDocument\(\)/);
 assert.match(html,/images:memoUploadImages\.length/);
});
test('exam document import is directly available in the exams section',()=>{
 assert.match(exams,/id="examImportFile"[^>]*accept="\.docx,\.pdf,\.png,\.jpg,\.jpeg,\.webp"/);
 assert.match(exams,/onclick="importExamDocument\(\)"/);
 assert.match(exams,/onclick="prepareImportedExamDraft\(\)"/);
 assert.match(exams,/id="examImportPreview"/);
});
test('exam file import is not hidden away only in the question bank',()=>{
 assert.doesNotMatch(html.slice(html.indexOf('<section id="questionBank"')),/id="examImportFile"/);
});
''',encoding='utf-8')
print('Applied 3.8.15 memo and exam file upload workflow')
