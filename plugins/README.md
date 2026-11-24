# Plugins

ارفع كل بلجن داخل مجلد مستقل باسم ثابت:

`plugins/<plugin-id>/`

التركيب المقترح:

```text
plugins/
  sample-plugin/
    addon.json
    icon.png
    install.sh
    screenshots/
      01.webp
      02.webp
    releases/
      1.0.0/
        package.ipk
```

- انسخ `templates/addons/addon.json.example` إلى `addon.json` واملأ بيانات البلجن.
- ارفع ملف الحزمة بصيغة IPK أو DEB أو ZIP أو TAR أو غيرها من الصيغ المدعومة.
- الصور داخل المجلد تُربط تلقائيًا بالكارت عند وجودها في `screenshots`، ويمكن تحديدها في `addon.json`.
- لا ترفع ملفًا أكبر من 80 MiB داخل Git؛ للحزم الأكبر استخدم GitHub Release وأضف رابطها في `package_url` داخل `addon.json`.
- اترك `compatibility_status` بقيمة `unverified` حتى يتم اختبار البلجن على صورة وجهاز محددين.
- لا ترفع ملفات طرف ثالث إلا بعد مراجعة حق إعادة التوزيع والحفاظ على نسب المطور الأصلي.

بعد رفع المجلد على فرع `main`، GitHub Actions يعيد بناء فهرس المكتبة تلقائيًا، ويظهر الكارت في صفحة `addons.html`. لا تحتاج لتعديل HTML أو JSON يدويًا.
