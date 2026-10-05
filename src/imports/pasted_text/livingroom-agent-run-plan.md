# خطة تشغيل وفحص وكيل Blender — الصالة

## التشغيل

شغّل السكربت مباشرة داخل Blender أو headless:

```bash
blender --background --python public/livingroom_blender.py -- --render
```

ولرندر تقديم العميل الرأسي:

```bash
blender --background --python public/livingroom_blender.py -- --portrait --render
```

السكربت ينشئ أو ينظف **`LivingRoom_Scene` فقط**؛ لا يمس `Kitchen_Scene` أو `Bedroom_Scene` أو `Bathroom_Scene`.

## فحص البنية

- القشرة: `LR_Floor`, `LR_Wall_*`, `LR_Ceiling`, `LR_Tray_*`, `LR_Cove_*`, `LR_Ceiling_Spot_0..4`, `LR_AC_*`.
- منطقة الجلوس: `LR_Sofa_*`, `LR_Pillow_0..4`, `LR_Throw_*`, `LR_Rug`, `LR_CoffeeTop`, `LR_CoffeeBase`, `LR_Coffee_Flute_*`, `LR_Chair_Drum/Back/Seat/Swivel`.
- التركيز البصري: `LR_Media_Back`, `LR_TV_Stone`, `LR_TV`, `LR_TV_Screen`, `LR_Fireplace_Cavity`, `LR_Flame_O_*`/`LR_Flame_I_*`, `LR_Fire_Glow`, `LR_Media_Console`, `LR_Console_Underglow`, `LR_Soundbar`, `LR_Shelf*`, `LR_Display_*`.
- الإطار والديكور: `LR_Sky_Outer/Inner`, `LR_Window`, `LR_Sheer_L/R` (بطيات متصلة)، `LR_Divider_*`, `LR_Tree_A_*`/`LR_Tree_B_*`, `LR_Side_Table_*`, `LR_Lamp_*`, `LR_Floor_Lamp_*`, `LR_Floor_*`.
- كاميرا: `LR_Camera_Main` و`LR_Camera_Portrait` بقيد `TRACK_TO` نحو `LR_Camera_Target`.

## فحص الرندر

1. تأكد أن الكاميرا ترى الفاصل الخشبي بشكل جانبي خفيف، السكشنال والطاولة في المقدمة، والنافذة خلفًا وحائط التلفاز يسارًا.
2. تأكد أن الكوف والسبوتات دافئة وغير محروقة، وأن الستائر بطيات **متصلة** شفافة (لا بيضاء صلبة ولا شرائح منفصلة)، وأن خلفية النافذة توهج ذهبي مسائي ناعم لا قرص محروق.
3. تأكد أن اللهب (`LR_Flame_*`) tongues متدرجة دافئة فوق سرير الموقد، وأن `LR_Fire_Glow` يلقي دفئًا على الحجر دون حرق.
4. افحص أن مناطق boucle والمحبوك والسجادة والحجر لا تبدو بلاستيكية أو بلا تفاصيل، وأن الوسائد بميلان/حجم متفاوت.
5. الرندر النهائي: `//livingroom_render.png` بدقة `1920×1080`، أو `//livingroom_portrait.png` بدقة `1080×1620`، Cycles و512 عينة وOpenImageDenoise.

## معايرة سريعة

- إذا كان المشهد قاتمًا: ارفع `LR_Window_Bounce` من 85 إلى 110W أو `Sky_Inner/Outer` قبل رفع الـ exposure.
- إذا احترق اللهب أو الأباجورات في الـbloom: خفّض `strength` لـ`Flame_Inner`/`Lamp_Shade`، أو استخدم AgX الذي يروّض القمم تلقائيًا.
- إذا احترق الكوف: خفّض `Warm_LED` من 6 إلى 4.5.
- إذا بدت الستائر معتمة: ارفع `emission strength` لخامة `Sheer` من 0.55، أو زد `alpha` قليلًا فوق 0.62.
- إذا اختفت تفاصيل الأقمشة: خفّض exposure إلى `0.0` وارفع عينات الرندر بدلًا من زيادة الإضاءة.
