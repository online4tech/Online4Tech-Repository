# Skins

ارفع كل Skin داخل مجلد مستقل باسم ثابت:

`skins/<skin-id>/`

التركيب المقترح:

```text
skins/
  sample-skin/
    addon.json
    icon.png
    install.sh
    screenshots/
      01.webp
      02.webp
    releases/
      1.0.0/
        skin.ipk
```

- استخدم `templates/addons/addon.json.example` كقالب بيانات.
- ارفع الحزمة بصيغة IPK أو DEB أو ZIP أو TAR أو غيرها من الصيغ المدعومة.
- أضف الأيقونة والصور داخل نفس مجلد السكين.
- لا ترفع ملفًا أكبر من 80 MiB داخل Git؛ للحزم الأكبر استخدم GitHub Release وضع رابطها في `package_url`.
- لا تضع حالة التوافق `tested` إلا بعد تجربة فعلية على صورة Enigma2 والجهاز المحددين.
- احتفظ بكل إصدار في مجلد مستقل ولا تستبدل الحزم المنشورة.

بعد الرفع، GitHub Actions يحدث فهرس الاسكينات تلقائيًا، وتظهر بطاقة السكين وصورها في صفحة `addons.html`.
