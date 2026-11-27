#!/usr/bin/env python3
from pathlib import Path
import os, re

root = Path(os.environ["PROJECT_ROOT"])
jp = root / "app/src/main/java/eg/alfardous/center/MainActivity.java"
hp = root / "app/src/main/assets/index.html"
gp = root / "app/build.gradle"
java = jp.read_text(encoding="utf-8")
html = hp.read_text(encoding="utf-8")
gradle = gp.read_text(encoding="utf-8")

if "AndroidBiometricBridge" not in java:
    java = java.replace(
        "import androidx.core.graphics.Insets;",
        "import androidx.biometric.BiometricManager;\nimport androidx.biometric.BiometricPrompt;\nimport androidx.core.content.ContextCompat;\nimport androidx.core.graphics.Insets;",
        1
    )
    java = java.replace(
        'web.addJavascriptInterface(new AndroidNotificationBridge(), "AndroidNotificationBridge");',
        'web.addJavascriptInterface(new AndroidNotificationBridge(), "AndroidNotificationBridge");\n        web.addJavascriptInterface(new AndroidBiometricBridge(), "AndroidBiometricBridge");',
        1
    )
    bridge = """
    public class AndroidBiometricBridge {
        private static final String PREFS = "alfardous_security";
        private static final String ENABLED = "biometric_enabled";

        private int allowedAuthenticators() {
            return Build.VERSION.SDK_INT >= Build.VERSION_CODES.R
                    ? BiometricManager.Authenticators.BIOMETRIC_WEAK | BiometricManager.Authenticators.DEVICE_CREDENTIAL
                    : BiometricManager.Authenticators.BIOMETRIC_WEAK;
        }

        @JavascriptInterface public boolean isAvailable() {
            try {
                return BiometricManager.from(MainActivity.this).canAuthenticate(allowedAuthenticators())
                        == BiometricManager.BIOMETRIC_SUCCESS;
            } catch (Exception e) { return false; }
        }

        @JavascriptInterface public boolean isEnabled() {
            return getSharedPreferences(PREFS, MODE_PRIVATE).getBoolean(ENABLED, false);
        }

        @JavascriptInterface public void enable() { authenticate(true); }
        @JavascriptInterface public void authenticate() { authenticate(false); }
        @JavascriptInterface public void disable() {
            getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(ENABLED, false).apply();
        }

        private void notifyResult(boolean success, boolean enabling, String message) {
            if (web == null) return;
            String js = "window.onBiometricAuthResult && window.onBiometricAuthResult("
                    + success + "," + enabling + "," + JSONObject.quote(message == null ? "" : message) + ");";
            web.evaluateJavascript(js, null);
        }

        private void authenticate(boolean enabling) {
            runOnUiThread(() -> {
                int authenticators = allowedAuthenticators();
                if (BiometricManager.from(MainActivity.this).canAuthenticate(authenticators)
                        != BiometricManager.BIOMETRIC_SUCCESS) {
                    notifyResult(false, enabling, "لا توجد بصمة أو وسيلة قفل متوافقة مهيأة على الجهاز. يمكنك استخدام كلمة مرور التطبيق.");
                    return;
                }
                BiometricPrompt prompt = new BiometricPrompt(MainActivity.this,
                        ContextCompat.getMainExecutor(MainActivity.this),
                        new BiometricPrompt.AuthenticationCallback() {
                            @Override public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                                if (enabling) {
                                    getSharedPreferences(PREFS, MODE_PRIVATE).edit().putBoolean(ENABLED, true).apply();
                                }
                                notifyResult(true, enabling, "");
                            }
                            @Override public void onAuthenticationError(int errorCode, CharSequence errString) {
                                notifyResult(false, enabling, errString == null ? "تعذر إكمال التحقق. استخدم كلمة مرور التطبيق." : errString.toString());
                            }
                        });
                BiometricPrompt.PromptInfo.Builder builder = new BiometricPrompt.PromptInfo.Builder()
                        .setTitle("حماية سنتر الفردوس")
                        .setSubtitle("تحقق بالبصمة أو قفل شاشة الهاتف");
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    builder.setAllowedAuthenticators(authenticators);
                } else {
                    builder.setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_WEAK)
                           .setNegativeButtonText("استخدام كلمة مرور التطبيق");
                }
                prompt.authenticate(builder.build());
            });
        }
    }

"""
    anchor = "    public class AndroidNotificationBridge {"
    if anchor not in java:
        raise SystemExit("AndroidNotificationBridge insertion point missing")
    java = java.replace(anchor, bridge + anchor, 1)
    java = java.replace(
        'web.removeJavascriptInterface("AndroidNotificationBridge");',
        'web.removeJavascriptInterface("AndroidNotificationBridge");\n            web.removeJavascriptInterface("AndroidBiometricBridge");',
        1
    )

if "androidx.biometric:biometric" not in gradle:
    gradle = gradle.replace(
        "dependencies {",
        "dependencies {\n    implementation 'androidx.biometric:biometric:1.1.0'",
        1
    )

# Add controls to the existing settings panel.
if 'id="biometricStatus"' not in html:
    anchor = '  <p class="hint">كلمة المرور محفوظة محليًا على هذا المتصفح. لا تستخدم كلمة مرور مهمة أو تستخدمها في حسابات أخرى.</p>'
    block = anchor + """
  <div class="panel" style="margin:12px 0;border:1px solid var(--gold)">
   <h3>فتح التطبيق بالبصمة أو قفل الهاتف</h3>
   <p class="hint">بعد فتح التطبيق بكلمة المرور مرة واحدة، يمكنك تفعيل التحقق ببصمة الإصبع أو قفل شاشة الهاتف. ستظل كلمة مرور التطبيق بديلًا عند الإلغاء أو عدم توفر التحقق.</p>
   <div class="actions"><button class="btn gold" type="button" onclick="enableBiometricUnlock()">تفعيل البصمة / قفل الهاتف</button><button class="btn light" type="button" onclick="disableBiometricUnlock()">إيقاف الفتح بالبصمة</button></div>
   <p id="biometricStatus" class="hint" aria-live="polite">حالة الفتح بالبصمة: غير مفعّل.</p>
  </div>"""
    if anchor not in html:
        raise SystemExit("Settings password hint anchor missing")
    html = html.replace(anchor, block, 1)

js = """
window.onBiometricAuthResult=function(success,enabling,message){
 const status=$('biometricStatus');
 if(success&&enabling){
  if(status)status.textContent='تم تفعيل الفتح بالبصمة أو قفل شاشة الهاتف. ستظل كلمة المرور متاحة كبديل.';
  alert('تم تفعيل الفتح بالبصمة أو قفل شاشة الهاتف.');
  return;
 }
 if(success&&!enabling){
  $('lockScreen')?.classList.add('hidden');
  if($('lockPassword'))$('lockPassword').value='';
  if($('lockConfirm'))$('lockConfirm').value='';
  return;
 }
 if(status)status.textContent=message||'لم يكتمل التحقق. استخدم كلمة مرور التطبيق.';
};
window.enableBiometricUnlock=function(){
 const bridge=window.AndroidBiometricBridge;
 if(!bridge||typeof bridge.enable!=='function'){alert('ميزة البصمة تحتاج نسخة أندرويد المحدثة.');return;}
 if(!bridge.isAvailable()){const msg='لا توجد بصمة أو وسيلة قفل متوافقة مهيأة على الجهاز. استخدم كلمة مرور التطبيق أو أعد إعداد قفل الهاتف.';$('biometricStatus').textContent=msg;alert(msg);return;}
 $('biometricStatus').textContent='اتبع نافذة أندرويد للتحقق وتفعيل الفتح الآمن.';
 bridge.enable();
};
window.disableBiometricUnlock=function(){
 const bridge=window.AndroidBiometricBridge;
 if(bridge&&typeof bridge.disable==='function')bridge.disable();
 if($('biometricStatus'))$('biometricStatus').textContent='تم إيقاف الفتح بالبصمة. ستظل كلمة مرور التطبيق مطلوبة.';
};
window.autoBiometricUnlock=function(){
 const bridge=window.AndroidBiometricBridge;
 if(!storageReady||!bridge||typeof bridge.isEnabled!=='function'||!bridge.isEnabled()||!bridge.isAvailable())return;
 if($('lockScreen')&&!$('lockScreen').classList.contains('hidden'))bridge.authenticate();
};
"""
if "window.autoBiometricUnlock=function()" not in html:
    anchor = "function openWhatsApp(text,phone=''){"
    if anchor not in html:
        raise SystemExit("JavaScript insertion point for biometric handlers missing")
    html = html.replace(anchor, js + "\n" + anchor, 1)

# Run the native prompt only after local storage and the password lock are ready.
html = html.replace(
    "render();updateServerStatus();initLock();",
    "render();updateServerStatus();initLock();if(window.autoBiometricUnlock)window.autoBiometricUnlock();",
    1
)

html = html.replace('content="3.8.16"', 'content="3.8.17"')
gradle = re.sub(r"versionCode\s+\d+", "versionCode 398", gradle)
gradle = re.sub(r"versionName\s+['\"][^'\"]+['\"]", "versionName '3.8.17'", gradle)

jp.write_text(java, encoding="utf-8")
hp.write_text(html, encoding="utf-8")
gp.write_text(gradle, encoding="utf-8")

readme = root / "README-AR.txt"
if readme.exists():
    r = readme.read_text(encoding="utf-8").replace("3.8.16", "3.8.17")
    r += "\n\nإضافة 3.8.17: فتح التطبيق بالبصمة أو قفل شاشة أندرويد بعد التفعيل من الإعدادات، مع بقاء كلمة مرور التطبيق بديلًا.\n"
    readme.write_text(r, encoding="utf-8")

for p in (root / "tests").glob("*.test.cjs"):
    t = p.read_text(encoding="utf-8")
    t = t.replace("3.8.16", "3.8.17").replace(r"3\\.8\\.16", r"3\\.8\\.17")
    t = t.replace("versionCode 397", "versionCode 398")
    p.write_text(t, encoding="utf-8")

(root / "tests/biometric-unlock.test.cjs").write_text(r'''const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const java=fs.readFileSync(path.join(root,'app/src/main/java/eg/alfardous/center/MainActivity.java'),'utf8');
const html=fs.readFileSync(path.join(root,'app/src/main/assets/index.html'),'utf8');
const gradle=fs.readFileSync(path.join(root,'app/build.gradle'),'utf8');

test('Android biometric bridge supports fingerprint and device credential with native fallback',()=>{
 assert.match(java,/class AndroidBiometricBridge/);
 assert.match(java,/BIOMETRIC_WEAK/);
 assert.match(java,/DEVICE_CREDENTIAL/);
 assert.match(java,/setNegativeButtonText\("استخدام كلمة مرور التطبيق"\)/);
 assert.match(java,/putBoolean\(ENABLED, true\)/);
 assert.match(java,/removeJavascriptInterface\("AndroidBiometricBridge"\)/);
 assert.match(gradle,/androidx\.biometric:biometric:1\.1\.0/);
});

test('biometric unlock can be enabled, disabled, and automatically requested after local storage is ready',()=>{
 assert.match(html,/id="biometricStatus"/);
 assert.match(html,/function enableBiometricUnlock|window\.enableBiometricUnlock=function/);
 assert.match(html,/window\.disableBiometricUnlock=function/);
 assert.match(html,/window\.autoBiometricUnlock=function/);
 assert.match(html,/initLock\(\);if\(window\.autoBiometricUnlock\)window\.autoBiometricUnlock\(\)/);
 assert.match(html,/window\.onBiometricAuthResult=function/);
});
''',encoding="utf-8")
print("Applied 3.8.17 native biometric/device-lock unlock and regression tests")
