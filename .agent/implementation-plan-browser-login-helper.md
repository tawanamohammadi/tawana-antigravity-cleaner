# Browser Login Helper - Implementation Plan
## پلن پیاده‌سازی کمک‌کننده ورود مرورگر

---

## 🎯 Objective | هدف

**English:**
Add safe, targeted browser cleaning and login assistance features to Antigravity Cleaner without deleting all user cookies. Focus on removing only Antigravity-related traces and optimizing network/browser state for successful login.

**فارسی:**
افزودن قابلیت‌های ایمن و هدفمند برای پاک‌سازی مرورگر و کمک به ورود موفق در Antigravity بدون حذف کل کوکی‌های کاربر. تمرکز روی حذف فقط ردهای مرتبط با Antigravity و بهینه‌سازی وضعیت شبکه/مرورگر.

---

## 📋 Features to Implement | قابلیت‌های پیاده‌سازی

### **1. Selective Browser Cleaning** | پاک‌سازی انتخابی مرورگر

**English:**
- Scan Chrome, Edge, Brave, and Firefox profiles
- Remove ONLY Antigravity-related data:
  - Cookies matching `antigravity`, `google.com/antigravity`, etc.
  - LocalStorage keys containing "antigravity"
  - Service Workers registered by Antigravity
  - Specific cache entries (not entire cache)
- Create backup before deletion
- Support multiple browser profiles (Default, Profile 1, Profile 2, etc.)

**فارسی:**
- اسکن پروفایل‌های Chrome، Edge، Brave و Firefox
- حذف فقط داده‌های مرتبط با Antigravity:
  - کوکی‌های شامل `antigravity`، `google.com/antigravity` و...
  - کلیدهای LocalStorage حاوی "antigravity"
  - Service Worker های ثبت‌شده توسط Antigravity
  - آیتم‌های خاص Cache (نه کل Cache)
- ایجاد Backup قبل از حذف
- پشتیبانی از چند پروفایل مرورگر

---

### **2. Session Backup & Restore** | پشتیبان‌گیری و بازیابی Session

**English:**
- After first successful login, backup valid session cookies
- Store encrypted in safe location: `~/.antigravity-cleaner/sessions/`
- Before launching Antigravity, restore saved session
- Auto-detect expired sessions and prompt re-login
- Support session validation (check if still valid)

**فارسی:**
- بعد از اولین ورود موفق، کوکی‌های معتبر session را backup بگیر
- ذخیره رمزنگاری‌شده در مکان امن: `~/.antigravity-cleaner/sessions/`
- قبل از اجرای Antigravity، session ذخیره‌شده را بازیابی کن
- تشخیص خودکار session های منقضی‌شده و درخواست ورود مجدد
- پشتیبانی از اعتبارسنجی session

---

### **3. Network Optimization for Login** | بهینه‌سازی شبکه برای ورود

**English:**
- Clear DNS cache (already implemented, enhance it)
- Test connectivity to Google servers (accounts.google.com, oauth2.googleapis.com)
- Detect and fix proxy/VPN conflicts
- Verify SSL certificate store integrity
- Reset browser network stack (separate from system network)
- Provide detailed diagnostic report

**فارسی:**
- پاک‌سازی DNS cache (قبلاً پیاده‌سازی شده، بهبود دادن)
- تست اتصال به سرورهای Google
- تشخیص و رفع تداخل‌های Proxy/VPN
- بررسی یکپارچگی SSL certificate store
- ریست کردن network stack مرورگر (جدا از شبکه سیستم)
- ارائه گزارش تشخیصی دقیق

---

### **4. Login State Cleaner** | پاک‌کننده وضعیت ورود

**English:**
- Clear stuck login states (half-completed OAuth flows)
- Remove corrupted authentication tokens
- Clean browser's credential manager (only Antigravity entries)
- Reset browser flags that might interfere with login
- Clear HSTS (HTTP Strict Transport Security) cache for Google domains

**فارسی:**
- پاک کردن وضعیت‌های ورود گیرکرده (OAuth flow های نیمه‌تمام)
- حذف token های احراز هویت خراب
- پاک‌سازی credential manager مرورگر (فقط ورودی‌های Antigravity)
- ریست کردن flag های مرورگر که ممکن است با ورود تداخل داشته باشند
- پاک کردن HSTS cache برای دامنه‌های Google

---

### **5. Browser Process Management** | مدیریت پروسس‌های مرورگر

**English:**
- Detect all running browser instances
- Gracefully close browsers before cleaning (save tabs if possible)
- Kill stuck browser processes
- Verify browser is fully closed before file operations
- Restart browser with clean state after operations

**فارسی:**
- تشخیص تمام نمونه‌های در حال اجرای مرورگر
- بستن نرم مرورگرها قبل از پاک‌سازی (ذخیره تب‌ها در صورت امکان)
- Kill کردن پروسس‌های گیرکرده مرورگر
- تایید بسته شدن کامل مرورگر قبل از عملیات روی فایل‌ها
- راه‌اندازی مجدد مرورگر با وضعیت پاک بعد از عملیات

---

## 🏗️ Technical Implementation | پیاده‌سازی فنی

### **File Structure | ساختار فایل‌ها**

```
src/
├── main.py                          # Main entry point (existing)
├── browser_helper.py                # NEW: Browser cleaning & session management
├── network_optimizer.py             # NEW: Network diagnostics & optimization
├── session_manager.py               # NEW: Session backup/restore with encryption
└── requirements.txt                 # Update with new dependencies

.agent/
└── logs/
    └── browser-helper-operations.log  # Detailed operation logs for debugging
```

---

### **New Dependencies | وابستگی‌های جدید**

```txt
# Existing
psutil
rich

# NEW additions
pycryptodome          # For session encryption
sqlite3               # Built-in, for cookie database access
requests              # For connectivity testing
```

---

### **Core Modules | ماژول‌های اصلی**

#### **1. BrowserHelper Class** (`browser_helper.py`)

**Methods:**
```python
class BrowserHelper:
    def __init__(self, logger)
    
    # Browser Detection
    def detect_installed_browsers(self) -> List[str]
    def get_browser_profiles(self, browser: str) -> List[str]
    
    # Selective Cleaning
    def clean_antigravity_cookies(self, browser: str, profile: str)
    def clean_antigravity_localstorage(self, browser: str, profile: str)
    def clean_antigravity_service_workers(self, browser: str, profile: str)
    def clean_antigravity_cache_entries(self, browser: str, profile: str)
    
    # Process Management
    def close_browser_gracefully(self, browser: str)
    def kill_browser_processes(self, browser: str)
    def is_browser_running(self, browser: str) -> bool
    
    # Backup
    def create_backup(self, file_path: str) -> str
    def restore_backup(self, backup_path: str)
```

---

#### **2. SessionManager Class** (`session_manager.py`)

**Methods:**
```python
class SessionManager:
    def __init__(self, storage_dir: str, logger)
    
    # Session Operations
    def backup_session(self, browser: str, profile: str) -> bool
    def restore_session(self, browser: str, profile: str) -> bool
    def validate_session(self, session_data: dict) -> bool
    def is_session_expired(self, session_data: dict) -> bool
    
    # Encryption
    def encrypt_session(self, data: dict) -> bytes
    def decrypt_session(self, encrypted: bytes) -> dict
    
    # Storage
    def save_session_to_disk(self, session_id: str, data: bytes)
    def load_session_from_disk(self, session_id: str) -> bytes
    def list_saved_sessions(self) -> List[dict]
```

---

#### **3. NetworkOptimizer Class** (`network_optimizer.py`)

**Methods:**
```python
class NetworkOptimizer:
    def __init__(self, logger)
    
    # Diagnostics
    def test_google_connectivity(self) -> dict
    def check_dns_resolution(self, domains: List[str]) -> dict
    def detect_proxy_settings(self) -> dict
    def verify_ssl_certificates(self) -> bool
    
    # Optimization
    def clear_browser_dns_cache(self, browser: str)
    def reset_browser_network_stack(self, browser: str)
    def fix_proxy_conflicts(self)
    def repair_ssl_certificate_store(self)
    
    # Reporting
    def generate_diagnostic_report(self) -> str
```

---

## 🎨 User Interface Changes | تغییرات رابط کاربری

### **New Menu Options | گزینه‌های منوی جدید**

```
Current Menu:
1. Quick Clean
2. Deep Clean
3. Network Reset
4. Full Repair
5. Toggle Dry Run
0. Exit

NEW Menu:
1. Quick Clean
2. Deep Clean
3. Network Reset
4. Full Repair
5. [NEW] Browser Login Helper          ← Main new feature
6. [NEW] Session Manager
7. Toggle Dry Run
0. Exit
```

---

### **Browser Login Helper Submenu | زیرمنوی کمک‌کننده ورود**

```
+----------------------------------------------------------+
|           BROWSER LOGIN HELPER | کمک‌کننده ورود          |
+----------------------------------------------------------+
| 1. Clean Antigravity Browser Traces (Safe)               |
|    پاک‌سازی ردهای Antigravity در مرورگر (ایمن)          |
|                                                          |
| 2. Optimize Network for Login                            |
|    بهینه‌سازی شبکه برای ورود                             |
|                                                          |
| 3. Clear Stuck Login States                              |
|    پاک کردن وضعیت‌های ورود گیرکرده                       |
|                                                          |
| 4. Run Full Login Repair (1+2+3)                         |
|    اجرای تعمیر کامل ورود                                 |
|                                                          |
| 5. Network Diagnostic Report                             |
|    گزارش تشخیصی شبکه                                     |
|                                                          |
| 0. Back to Main Menu                                     |
+----------------------------------------------------------+
```

---

### **Session Manager Submenu | زیرمنوی مدیریت Session**

```
+----------------------------------------------------------+
|         SESSION MANAGER | مدیریت نشست‌ها                  |
+----------------------------------------------------------+
| 1. Backup Current Session                                |
|    پشتیبان‌گیری از Session فعلی                          |
|                                                          |
| 2. Restore Saved Session                                 |
|    بازیابی Session ذخیره‌شده                             |
|                                                          |
| 3. List All Saved Sessions                               |
|    لیست تمام Session های ذخیره‌شده                       |
|                                                          |
| 4. Delete Old Sessions                                   |
|    حذف Session های قدیمی                                 |
|                                                          |
| 0. Back to Main Menu                                     |
+----------------------------------------------------------+
```

---

## 🔒 Safety Measures | اقدامات ایمنی

**English:**
1. **Always create backups** before deleting any browser data
2. **Verify browser is closed** before file operations
3. **Encrypt sensitive data** (sessions, cookies) at rest
4. **Detailed logging** of all operations for debugging
5. **Dry-run mode** support for all new features
6. **User confirmation** for potentially risky operations
7. **Rollback capability** if something goes wrong

**فارسی:**
1. **همیشه Backup بگیر** قبل از حذف هر داده مرورگر
2. **تایید بسته بودن مرورگر** قبل از عملیات روی فایل‌ها
3. **رمزنگاری داده‌های حساس** (session ها، کوکی‌ها)
4. **لاگ دقیق** تمام عملیات برای دیباگ
5. **پشتیبانی از حالت Dry-run** برای تمام قابلیت‌های جدید
6. **تایید کاربر** برای عملیات‌های پرخطر
7. **قابلیت Rollback** در صورت بروز مشکل

---

## 📊 Logging Strategy | استراتژی لاگ‌گیری

### **Log Levels | سطوح لاگ**

```python
DEBUG:   Detailed technical operations (cookie queries, file paths)
INFO:    User-facing actions (started cleaning, found X items)
WARNING: Potential issues (browser still running, backup failed)
ERROR:   Operation failures (cannot access database, permission denied)
```

### **Log File Location | مکان فایل لاگ**

```
Primary:   ~/Desktop/Antigravity-Cleaner.log          (User-facing, existing)
Detailed:  .agent/logs/browser-helper-operations.log  (Developer/debugging, NEW)
```

### **Log Format | فرمت لاگ**

```
[2025-12-10 21:06:17] [INFO] Starting selective browser cleaning...
[2025-12-10 21:06:18] [DEBUG] Detected browsers: Chrome, Edge
[2025-12-10 21:06:18] [DEBUG] Chrome profiles found: Default, Profile 1
[2025-12-10 21:06:19] [INFO] Scanning Chrome Default profile...
[2025-12-10 21:06:19] [DEBUG] Cookie DB: C:\Users\...\Cookies
[2025-12-10 21:06:20] [INFO] Found 3 Antigravity-related cookies
[2025-12-10 21:06:20] [DEBUG] Cookies: [SID=..., HSID=..., antigravity_session=...]
[2025-12-10 21:06:21] [INFO] Creating backup: cookies_backup_20251210_210621.db
[2025-12-10 21:06:22] [INFO] Deleted 3 cookies successfully
[2025-12-10 21:06:22] [INFO] ✓ Browser cleaning completed
```

---

## 🧪 Testing Plan | پلن تست

**English:**
1. Test on Windows 10/11 with Chrome, Edge, Brave
2. Test with multiple browser profiles
3. Test session backup/restore cycle
4. Test network diagnostics on different network conditions
5. Test rollback functionality
6. Test with browser running vs closed
7. Verify no data loss for non-Antigravity cookies

**فارسی:**
1. تست روی Windows 10/11 با Chrome، Edge، Brave
2. تست با چند پروفایل مرورگر
3. تست چرخه backup/restore سشن
4. تست تشخیص شبکه در شرایط مختلف
5. تست قابلیت Rollback
6. تست با مرورگر باز و بسته
7. تایید عدم از دست رفتن داده برای کوکی‌های غیر-Antigravity

---

## 📈 Success Metrics | معیارهای موفقیت

**English:**
- ✅ Successfully removes only Antigravity-related browser data
- ✅ No user data loss (other cookies, passwords, history remain intact)
- ✅ Session backup/restore works across browser restarts
- ✅ Network diagnostics accurately identify login issues
- ✅ Improves login success rate by at least 70%
- ✅ All operations logged for debugging
- ✅ Rollback works if needed

**فارسی:**
- ✅ فقط داده‌های مرتبط با Antigravity حذف شود
- ✅ داده‌های کاربر از دست نرود (کوکی‌ها، پسوردها، تاریخچه سالم بماند)
- ✅ Backup/Restore سشن بعد از ریستارت مرورگر کار کند
- ✅ تشخیص شبکه مشکلات ورود را دقیق شناسایی کند
- ✅ نرخ موفقیت ورود حداقل ۷۰٪ بهبود یابد
- ✅ تمام عملیات برای دیباگ لاگ شود
- ✅ Rollback در صورت نیاز کار کند

---

## 🚀 Implementation Order | ترتیب پیاده‌سازی

1. **Phase 1:** Create logging infrastructure (.agent/logs/)
2. **Phase 2:** Implement BrowserHelper (selective cleaning)
3. **Phase 3:** Implement NetworkOptimizer (diagnostics)
4. **Phase 4:** Implement SessionManager (backup/restore)
5. **Phase 5:** Integrate into main.py menu system
6. **Phase 6:** Testing and refinement
7. **Phase 7:** Update README and documentation

---

## 📝 Notes for Agent | یادداشت‌ها برای ایجنت

**English:**
- This plan prioritizes SAFETY over aggressiveness
- Always backup before delete
- Focus on Antigravity-specific data only
- Provide clear user feedback at each step
- Log everything for debugging
- Support dry-run mode for all operations

**فارسی:**
- این پلن ایمنی را بر تهاجمی بودن ترجیح می‌دهد
- همیشه قبل از حذف Backup بگیر
- فقط روی داده‌های خاص Antigravity تمرکز کن
- در هر مرحله بازخورد واضح به کاربر بده
- همه چیز را برای دیباگ لاگ کن
- از حالت Dry-run برای تمام عملیات پشتیبانی کن

---

**Plan Version:** 1.0  
**Created:** 2025-12-10  
**Author:** Antigravity Cleaner Development Team
