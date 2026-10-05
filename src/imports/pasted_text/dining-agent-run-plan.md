# خطة تشغيل وفحص وكيل Blender — السفرة

## التشغيل

```bash
blender --background --python public/dining_blender.py -- --render
```

ولرندر تقديم العميل الرأسي:

```bash
blender --background --python public/dining_blender.py -- --portrait --render
```

السكربت ينشئ أو ينظف **`Dining_Scene` فقط**؛ لا يمس مشاهد المطبخ/النوم/الحمام/الصالة.

## فحص البنية

- القشرة: `DR_Floor`, `DR_Wall_*`, `DR_Ceiling`, `DR_Tray_*`, `DR_Cove_*`, `DR_Ceiling_Spot_0..3`.
- الطاولة: `DR_Table_Top` (بيضاوية)، `DR_Table_Ped`, `DR_Ped_Flute_*`, `DR_Table_Foot`.
- التنسيق: `DR_Runner`, `DR_Bowl`, `DR_Branch_*`, `DR_Taper_*`/`DR_Wick_*`, `DR_Plate_*`/`DR_Plate_In_*`.
- المقاعد: `DR_Chair_0..5` (كل واحد: `_Seat`, `_Back`, `_Back_Curve`, `_Leg_*`).
- الإضاءة البطولية: `DR_Ring_0/1`, `DR_Rod_*`, `DR_Canopy`, `DR_Chandelier_Key/Fill`.
- الجدران والديكور: `DR_Feature_Slat_*`, `DR_Art*`, `DR_Sky_Outer/Inner`, `DR_Window`, `DR_Sheer_L/R`, `DR_Buffet*`, `DR_Mirror*`, `DR_Pampas_*`, `DR_Tree_*`.
- كاميرا: `DR_Camera_Main` و`DR_Camera_Portrait` بقيد `TRACK_TO` نحو `DR_Camera_Target`.

## فحص الرندر

1. تأكد أن الكاميرا ترى الطاولة والكراسي في المقدمة، النافذة خلفًا، حائط الجوز المضلّع يسارًا، والبوفيه يمينًا.
2. تأكد أن الثريا الحلقتين معلّقة فوق مركز الطاولة وتلقي دفئًا دون حرق (روّض بـAgX أو خفّض `Chandelier_Ring` strength).
3. تأكد أن الستائر بطيات متصلة شفافة وخلفية النافذة توهج ذهبي مسائي ناعم.
4. افحص أن boucle المقاعد والسجادة والترافرتين لا تبدو بلاستيكية، وأن الأطباق والشموع مقروءة على الطاولة.
5. الرندر النهائي: `//dining_render.png` بدقة `1920×1080`، أو `//dining_portrait.png` بدقة `1080×1620`، Cycles و512 عينة وOpenImageDenoise.

## معايرة سريعة

- إذا كان المشهد قاتمًا: ارفع `DR_Room_Bounce` أو `Sky_Inner/Outer` قبل رفع الـexposure.
- إذا احترقت الثريا/الشموع في الـbloom: خفّض `strength` لـ`Chandelier_Ring`/`Flame`.
- إذا احترق الكوف: خفّض `Warm_LED` من 6 إلى 4.5.
- إذا اختفت تفاصيل الأقمشة: خفّض exposure إلى `0.0` وارفع عينات الرندر بدلًا من زيادة الإضاءة.
