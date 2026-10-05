# خطة تنفيذ الـ AI Agent على Blender — الحمام الفاخر (Bathroom)

خطة إجرائية يتبعها وكيل ذكاء اصطناعي متصل بـ Blender (عبر MCP / socket server على المنفذ `9876`، أو تشغيل مباشر بـ headless) لبناء مشهد الحمام من `public/bathroom_blender.py`، والتحقق من صحته، وإخراج رندر نهائي مطابق للصورة المرجعية `src/imports/ref_bathroom.jpg`.

الملف المصدر: **`public/bathroom_blender.py`** (آخر إصدار — بعد إصلاح اتجاهات الأسطوانات والمرحاض).

---

## 0) المتطلبات المسبقة (Preconditions)
- Blender 3.6+ أو 4.x مثبّت، مع تفعيل GPU لـ Cycles إن أمكن.
- الاتصال بـ Blender متاح (MCP `blender` / socket على `127.0.0.1:9876`) **أو** مسار تنفيذ `blender --background --python`.
- نسخة `bathroom_blender.py` منقولة إلى بيئة Blender أو مقروءة كنص لإرسالها للسيرفر.

---

## 1) تنظيف وتحضير المشهد
1. تأكد من عدم وجود مشهد نشط ملوّث: السكربت يستدعي `clear_scene()` أول `main()` فيحذف كل الكائنات والخامات والإضاءات والكاميرات — لا حاجة لتنظيف يدوي.
2. إن كنت تعمل داخل ملف `.blend` يحوي المطبخ/الأوضة، أنشئ Scene جديدة باسم `Bathroom_Scene` قبل التشغيل حفاظاً على المشاهد الأخرى.

## 2) تشغيل السكربت
- **مسار A (socket/MCP):** أرسل محتوى `bathroom_blender.py` كـ `exec_code` إلى سيرفر Blender. انتظر رجوع `status: success`.
- **مسار B (headless):**
  ```
  blender --background --python public/bathroom_blender.py -- --render
  ```
- راقب الـ stdout؛ يجب أن يظهر تسلسل الطباعة كاملاً وينتهي بـ:
  `Scene complete: N objects | M materials`.
- **معيار نجاح:** لا استثناءات (`Traceback`)، و`N > 120` كائن تقريباً و`M ≈ 40+` خامة.

## 3) الفحص البنيوي (Structural checks — عبر استعلامات bpy)
نفّذ استعلامات تأكيدية داخل Blender وتحقق من وجود المجموعات التالية بالأسماء:
- **القشرة:** `Floor`, `Wall_Back/Left/Right`, `Ceiling`, `Tray_*`, `Cove_0..3`, `Rec_Ring_*`/`Rec_Disc_*`, `Skirt_*`.
- **الجدار المميز:** `Pillar_Back`, `Pillar_Slat_*` (عمودية)، `HNiche_Back`, `HNiche_LED`, `HNiche_Item_0..4`, `HNiche_Vase`.
- **الفانيتي:** `Vanity_Body`, `Vanity_Slat_0..19` (**عمودية** — تأكد `rotation_euler ≈ 0**)، `Vanity_Top`, `Vanity_LED`, `Vessel_Bowl`, `Vessel_Rim` (**أفقية**), `Faucet_*`, `Soap_*`, `Candle*`, `Vanity_Vase`, `Vanity_Towel`.
- **المرآة/التعليقة:** `Mirror_Halo/Rim/Glass`, `Pend_*`.
- **البانيو:** `Tub_Shell` (scale.y≈0.66), `Tub_Rim`, `Tub_Inner`, `Tub_Bottom`, `Tub_Escutcheon`, `Tub_Spout_Arm` (**أفقي على الجدار الخلفي**), `Tub_Spout_Down`, `Tub_Valve`, `Tub_Caddy`.
- **عمود النيش:** `NC_Back/JambL/JambR/Top/Base`, `NC_Shelf_0..4` (**5 أرفف**), `NC_ShelfLED_0..4`, `NC_Item_*`, `NC_Pt`.
- **الدش:** `Glass_Front/Return`, `Frame_*`, `Door_Handle`, `Rain_*`, `Shower_Ctrl`, `Slide_Bar`, `Hand_Arm/Head`, `SNiche_*`.
- **المرحاض/اللوحة:** `WC_Cistern` (**تأكد أبعاده طبيعية وليست شبه معدومة**), `WC_Flush`, `WC_Bowl`, `WC_Seat`, `WC_TP_*`, `Art_Frame/Face`, `Art_Leaf_*`.
- **الأرضيات/الديكور:** `Rug`, `Rug_Inner`, `Decor_Vase`, `Decor_Branch_*`.
- **الإضاءة:** `Key_Sun`, `Fill_Cam`, `Bounce`, `Vanity_Fill`، وخمس وحدات `Ceiling_Spot_0..4` (تأكد أن `spot_size≈55°` و`spot_blend≈0.72` وموجهة رأسيًا للأسفل)، ونقاط `*_Pt`، وكاميرا `Cam_Main` بقيد `TRACK_TO` نحو `Cam_Target`.

## 4) فحص الكاميرا والإطار
- تأكد `Cam_Main.location ≈ (-0.5, 7.2, 1.65)` و`Cam_Target ≈ (-0.15, -0.6, 1.0)`، و`sensor_fit = VERTICAL`، `angle_y = radians(44)`.
- التقط **لقطة Viewport** من زاوية الكاميرا وقارنها بصرياً بـ `ref_bathroom.jpg`:
  - الفانيتي الطويلة والمرآة المدوّرة على **اليسار**.
  - البانيو مركزي أمام النيش الأفقي، والعمود المخدد يساره، وعمود النيش ذو الـ5 أرفف في **الركن الأيسر**.
  - الدش الزجاجي في **الركن الخلفي الأيمن**، والمرحاض واللوحة على **اليمين**.

## 5) الرندر النهائي (Cycles)
- الإعدادات مضبوطة داخل `setup_render()`: `CYCLES` + `GPU` + `AgX` (سقوط تلقائي إلى Filmic) + `OpenImageDenoise` + `512` عينة + `1920×1080`.
- شغّل الرندر (`bpy.ops.render.render(write_still=True)` أو F12). المخرج: `//bathroom_render.png` بجوار ملف `.blend`.
- **معيار نجاح:** صورة خالية من النويز، دفء greige واضح، إكسسوارات سوداء مطفية، وهج LED دافئ في الكوف/النيش/تحت الفانيتي.

## 6) حلقة المعايرة (Iterate — عند الحاجة)
عدّل هذه المقابض في أعلى السكربت أو داخل الدوال ثم أعد التشغيل:
- **إضاءة زائدة/ناقصة:** شدّات `Key_Sun` (1.6)، `Fill_Cam` (0.55)، ونقاط `*_Pt`.
- **قوة الـ LED:** `emission_strength` في خامات `led_*`/`halo` (7–8).
- **عمق المجال:** `cam.data.dof.focus_distance` (6.2) و`aperture_fstop` (6.0).
- **سرعة المعاينة:** خفّض `SAMPLES` إلى 128 أثناء المعايرة ثم ارفعه لـ512 للنهائي.

## 7) التسليم
- احفظ `bathroom_render.png` و(اختيارياً) `bathroom_scene.blend`.
- أرجِع تقريراً: عدد الكائنات/الخامات، لقطة Viewport، الرندر النهائي، وأي انحرافات عن الصورة المرجعية.

---

### ملاحظات هندسية مهمة للوكيل (تفادي أخطاء شائعة)
- **تحويل المحاور:** Three→Blender عبر `T(x,y,z)=(x,z,y)`؛ الجدار الخلفي عند `y=-3`، الكاميرا أمام عند `y=+7.2`.
- **الأسطوانات الأفقية:** لجعل أسطوانة (محورها Z) تمتد على X استخدم `rot=(0,90,0)`؛ ولتمتد على Y (العمق) استخدم `rot=(90,0,0)`. `rot=(0,0,90)` **لا يغيّر** اتجاه أسطوانة عمودية (خطأ شائع تم إصلاحه في هذا الإصدار).
- **التوري (Torus):** الوضع الافتراضي أفقي (مستوى XY) — مناسب لحلقات الأحواض/البانيو؛ استخدم `rot=(0,90,0)` فقط لإطار المرآة المواجه للغرفة.
