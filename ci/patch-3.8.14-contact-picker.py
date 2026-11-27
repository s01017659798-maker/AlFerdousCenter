#!/usr/bin/env python3
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_ROOT"])
java_path = root / "app/src/main/java/eg/alfardous/center/MainActivity.java"
html_path = root / "app/src/main/assets/index.html"
java = java_path.read_text(encoding="utf-8")
html = html_path.read_text(encoding="utf-8")

def once(old, new, label, source):
    if old in source:
        return source.replace(old, new, 1)
    raise SystemExit("Missing patch anchor: " + label)

# Native Android phone picker: system picker grants access to the chosen number only.
if "AndroidContactBridge" not in java:
    java = once("import android.provider.MediaStore;", "import android.provider.MediaStore;\nimport android.provider.ContactsContract;\nimport android.database.Cursor;", "Android contact imports", java)
    java = once("private static final int FILE_PICKER = 4207;", "private static final int FILE_PICKER = 4207;\n    private static final int CONTACT_PICKER = 4209;", "contact request code", java)
    java = once('private String pendingName = "export";', 'private String pendingContactTarget = "phone";\n    private String pendingName = "export";', "pending contact target", java)
    java = once('web.addJavascriptInterface(new AndroidFileBridge(), "AndroidFileBridge");', 'web.addJavascriptInterface(new AndroidFileBridge(), "AndroidFileBridge");\n        web.addJavascriptInterface(new AndroidContactBridge(), "AndroidContactBridge");', "contact bridge registration", java)
    bridge = """
    public class AndroidContactBridge {
        @JavascriptInterface public void pickPhone(String target) {
            runOnUiThread(() -> {
                pendingContactTarget = (target == null || target.trim().isEmpty()) ? "phone" : target;
                try {
                    Intent intent = new Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI);
                    startActivityForResult(intent, CONTACT_PICKER);
                } catch (Exception e) {
                    Toast.makeText(MainActivity.this, "تعذر فتح جهات الاتصال", Toast.LENGTH_SHORT).show();
                }
            });
        }
    }

"""
    java = once("    public class AndroidNotificationBridge {", bridge + "    public class AndroidNotificationBridge {", "contact bridge class", java)
    activity_anchor = "        if (requestCode == FILE_PICKER) {"
    contact_result = """        if (requestCode == CONTACT_PICKER) {
            if (resultCode == RESULT_OK && data != null && data.getData() != null && web != null) {
                String name = "";
                String number = "";
                try (Cursor cursor = getContentResolver().query(data.getData(),
                        new String[]{ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                                ContactsContract.CommonDataKinds.Phone.NUMBER}, null, null, null)) {
                    if (cursor != null && cursor.moveToFirst()) {
                        name = cursor.getString(0);
                        number = cursor.getString(1);
                    }
                } catch (Exception ignored) { }
                String js = "window.onAndroidContactPicked && window.onAndroidContactPicked("
                        + JSONObject.quote(pendingContactTarget) + ","
                        + JSONObject.quote(name == null ? "" : name) + ","
                        + JSONObject.quote(number == null ? "" : number) + ");";
                web.evaluateJavascript(js, null);
            }
            return;
        }
"""
    java = once(activity_anchor, contact_result + activity_anchor, "contact result handler", java)
    java = once('web.removeJavascriptInterface("AndroidFileBridge");', 'web.removeJavascriptInterface("AndroidFileBridge");\n            web.removeJavascriptInterface("AndroidContactBridge");', "remove contact bridge", java)

# Replace unsupported-only Web Contacts behavior with the Android native picker first.
pattern = re.compile(r"async function pickPhoneContact\(target\)\{.*?\n\}", re.S)
replacement = """function pickPhoneContact(target){
 const input=$(target);if(!input)return;
 if(window.AndroidContactBridge&&typeof AndroidContactBridge.pickPhone==='function'){
  AndroidContactBridge.pickPhone(target);return;
 }
 if(navigator.contacts&&typeof navigator.contacts.select==='function'){
  navigator.contacts.select(['tel'],{multiple:false}).then(contacts=>{
   const tel=contacts?.[0]?.tel?.[0];if(tel){input.value=normalizeCenterPhone(tel);input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));}
  }).catch(err=>{if(err?.name!=='AbortError')alert('تعذر قراءة جهة الاتصال. يمكنك إدخال الرقم يدويًا.');});
  return;
 }
 alert('اختيار جهات الاتصال غير متاح هنا. يمكنك إدخال الرقم يدويًا.');
}
window.onAndroidContactPicked=function(target,name,number){
 const input=$(target);if(!input||!number)return;
 input.value=normalizeCenterPhone(number);
 input.dispatchEvent(new Event('input',{bubbles:true}));
 input.dispatchEvent(new Event('change',{bubbles:true}));
};"""
html, count = pattern.subn(replacement, html, count=1)
if count != 1:
    raise SystemExit("Could not replace pickPhoneContact()")

# Bump beyond the already-created 3.8.13 package.
html = html.replace("3.8.13", "3.8.14")
html_path.write_text(html, encoding="utf-8")
java_path.write_text(java, encoding="utf-8")

gradle_path = root / "app/build.gradle"
gradle = gradle_path.read_text(encoding="utf-8")
gradle = re.sub(r"versionCode\\s+\\d+", "versionCode 395", gradle)
gradle = re.sub(r"versionName\\s+['\"][^'\"]+['\"]", "versionName '3.8.14'", gradle)
gradle_path.write_text(gradle, encoding="utf-8")

for test_path in (root / "tests").glob("*.test.cjs"):
    test = test_path.read_text(encoding="utf-8")
    test = test.replace("3.8.13", "3.8.14")
    test = test.replace("versionCode 394", "versionCode 395")
    test_path.write_text(test, encoding="utf-8")

contact_test = root / "tests/contact-picker.test.cjs"
contact_test.write_text(r'''const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'app/src/main/assets/index.html'), 'utf8');
const java = fs.readFileSync(path.join(root, 'app/src/main/java/eg/alfardous/center/MainActivity.java'), 'utf8');

test('native Android contact picker is wired for student, guardian, and teacher phone fields', () => {
  assert.match(html, /pickPhoneContact\('phone'\)/);
  assert.match(html, /pickPhoneContact\('guardian'\)/);
  assert.match(html, /pickPhoneContact\('teacherPhone'\)/);
  assert.match(html, /AndroidContactBridge\.pickPhone\(target\)/);
  assert.match(html, /window\.onAndroidContactPicked=function\(target,name,number\)/);
  assert.match(java, /ContactsContract\.CommonDataKinds\.Phone\.CONTENT_URI/);
  assert.match(java, /startActivityForResult\(intent, CONTACT_PICKER\)/);
  assert.match(java, /ContactsContract\.CommonDataKinds\.Phone\.NUMBER/);
  assert.match(java, /web\.evaluateJavascript\(js, null\)/);
  assert.match(java, /removeJavascriptInterface\("AndroidContactBridge"\)/);
  assert.doesNotMatch(java, /READ_CONTACTS/);
});
''', encoding="utf-8")
print("Applied 3.8.14 native Android contact picker and regression test")
