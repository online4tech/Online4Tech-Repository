# Backups

ارفع كل نسخة احتياطية في مجلد مستقل حسب الشركة والموديل والإصدار:

```text
backups/
  vuplus/
    vu-zero-4k/
      openatv-8-0-1-20261124/
        backup.json
        cover.webp
        screenshots/
          01.webp
          02.webp
```

- انسخ `templates/backups/backup.json.example` إلى `backup.json` واملأ بيانات النسخة.
- ارفع الغلاف والصور داخل نفس مجلد النسخة؛ ستظهر تلقائيًا في كارت النسخة وصفحتها.
- لو ملف الباك أب أصغر من 80 MiB يمكن وضعه داخل المجلد. الملفات الأكبر لا تُرفع داخل Git؛ ارفعها كـ Asset في GitHub Release ثم ضع رابطها المباشر في `package_url`.
- يجب أن يحدد `device_model` الموديل بدقة، ولا تخلط صور أو ملفات موديلات مختلفة.
- لا ترفع إعدادات اشتراكات أو كلمات مرور أو بيانات شخصية أو ملفات حساسة.
- كل نسخة جديدة لها مجلد مستقل؛ لا تستبدل نسخة قديمة.

بعد رفع المجلد على `main`، GitHub Actions يحدث `catalog/uploads/backups.json` تلقائيًا، وتظهر النسخة الجديدة في قسم «النسخ المضافة حديثًا» بصفحة `receiver-backups.html`.

## طرق رفع الباك أب

- **الأسرع لملف موجود على الكمبيوتر:** افتح [صفحة Releases](https://github.com/online4tech/Online4Tech-Repository/releases)، أنشئ Release، أرفق ملف الباك أب والصور، ثم انشره. لا تحتاج إلى إنشاء `backup.json` يدويًا.
- **GitHub Desktop / Git:** استخدمه للمجلدات والملفات التي تناسب حدود Git العادية. لا ترفع ملفًا أكبر من 100 MiB داخل Git؛ استخدم Releases بدلًا منه.
- **GitHub Actions:** استخدم [Backup Release Publisher](https://github.com/online4tech/Online4Tech-Repository/actions/workflows/backup-release-publisher.yml) لإحضار ملف من رابط تنزيل سحابي مباشر ورفعه إلى Release دون تنزيله على جهازك.

لرفع Release من الموقع، يفضّل أن يكون العنوان بالشكل: `Backup | Brand | Exact Model | Version`. ويمكن إضافة بيانات عادية في وصف Release مثل `Brand:` و`Model:` و`Version:` و`Date:` و`Description:` و`Compatibility:`. بعد النشر، ينشئ GitHub Actions ملف `backup.json` تلقائيًا داخل `catalog/uploads/release-backups/` ويحدّث فهرس الصفحة.

راجع [دليل طرق الرفع الثلاثة](../docs/BACKUP-UPLOAD-GUIDE.md) للتفاصيل.
