# Cinematic Architectural Flythrough — Implementation Plan

## القرار التنفيذي

- **الماستر:** 36 ثانية / 864 إطاراً / 24fps. هذه مدة كافية لقراءة الخامات من دون إبطاء الإيقاع.
- **التسليم:** نسختان مصممتان كمسارين منفصلين: `16:9` (3840×2160) و`9:16` (2160×3840). لا تعتمد نسخة عمودية على crop.
- **الحركة:** Cinematic flythrough، لا FPV رياضي. Banking حتى 3° في المنعطفات الطويلة فقط، Ease-in/out واضح، وأي قرب من أثاث أو جدار يبقى على مسافة 35–50 سم على الأقل.
- **العدسات:** 24mm للقطات المفتوحة، 28–35mm للممرات والجناح الخاص. لا تستخدم 21mm داخل الممر.

## المواصفات التقنية

| بند | اعتماد |
| --- | --- |
| Frame rate | 24fps ثابت من Blender حتى الـfinal export |
| Shutter | 180° / 0.5 frame، مع تقليل سرعة الـpan عند التفاصيل الخطية |
| Render | Cycles، OpenEXR Half (16-bit float)، multilayer عند الحاجة |
| Color | Linear/scene-referred → DaVinci Wide Gamut Intermediate → Rec.709 Gamma 2.4 |
| Denoise | OIDN أو OptiX على passes قبل compositing؛ راجع البوكلي والحجر عند 100% |
| الصوت | Minimal cinematic ambient: room tone، air movement، fabric/footstep micro-detail، swell واحد فقط عند الـHero |

## Lock قبل التحريك

1. ثبّت أبعاد كل غرفة ومواضع العناصر الكبيرة قبل رسم المسارات.
2. أضف `TRANSIT_OCCLUDER` لكل انتقال محجوب: ضلع باب، عمود، طرف جدار، أو ظهر كرسي. لا تُنشئ الانتقال في المونتاج وحده.
3. اعمل render still لكل خامة تحت ضوء النهار وضوء 2700–3000K قبل الرندر المتحرك.
4. اعمل playblast بلا motion blur؛ افحص clipping، سرعة الدوران، والـvertical composition أولاً.

## Timeline — 16:9 master (864 frames)

| Frames | الزمن | اللقطة / الحركة | الانتقال المقصود |
| --- | --- | --- | --- |
| 001–048 | 00:00–00:02 | Dark close-up: ملمس walnut/bronze في المدخل، تركيز على حافة مضيئة. حركة أمامية 20–30cm فقط. | Rack focus من الحافة إلى عمق المدخل عند F032. |
| 049–096 | 00:02–00:04 | Partial reveal: تمر الكاميرا خلف ضلع مدخل أو فاصل خشبي وتكشف جزءاً من الصالة. | Foreground occlusion عند F072–F090. |
| 097–192 | 00:04–00:08 | Hero reveal أول: الصالة، البوكلي، وجدار التلفاز. حركة lateral هادئة، لا pan سريع. | settle بصري عند F156. |
| 193–288 | 00:08–00:12 | اقترب بمحاذاة الكنب نحو الترافرتين. ارفع العين 10–15cm فقط. | Match cut texture: travertine detail عند F270. |
| 289–384 | 00:12–00:16 | جزيرة المطبخ وواجهات walnut. لا تلف حول الجزيرة؛ مسار مائل مستقيم مع foreground stool. | Shadow wipe تحت pendant / stool عند F360–F384. |
| 385–480 | 00:16–00:20 | السفرة باتجاه التراس. rack focus من حلقة برونزية إلى الضوء الخارجي. | Rack focus يبدأ F416 ويكتمل F448. |
| 481–576 | 00:20–00:24 | دخول الممر، عدسة 32–35mm، محور كاميرا قريب من المنتصف. | Doorframe occlusion F552–F576. |
| 577–672 | 00:24–00:28 | جناح النوم: linen/bedside glow وخامة البلاستر. لا تدخل بعمق يفرض رجوعاً سريعاً. | Match cut بين line of bedside light وخط إضاءة الصالة، F648–F672. |
| 673–768 | 00:28–00:32 | انتقال مبرر بصرياً إلى الصالة عبر foreground dark wall / cut مخفي. | Shadow wipe F696–F720. |
| 769–864 | 00:32–00:36 | Hero frame النهائي: الصالة والتراس، rise تدريجي 25–40cm وميل خفيف جداً. | موسيقيّاً: swell عند F792، hold نهائي F840–F864. |

### قواعد الحركة عند 24fps

- لا تجعل عنصراً رأسياً عالي التباين يعبر عرض الكادر في أقل من ~7 ثوانٍ.
- اسمح للمسار بالتباطؤ قبل وبعد كل occlusion؛ لا تغيّر اتجاه الكاميرا داخل منطقة الحجب.
- استخدم منحنيات Bezier وAuto Clamped handles. لا تستخدم linear interpolation إلا لاختبار أولي.
- حافظ على Horizon قريباً من مستوى العين؛ الارتفاع النهائي هو الاستثناء الوحيد المقصود.

## Timeline — 9:16 master (864 frames)

المحتوى الزمني نفسه، لكن الـblocking مختلف: امنح الأولوية للارتفاع، الستائر، الـpendants، الأعمدة، وتتابع مستويات الضوء.

| Frames | التركيب العمودي |
| --- | --- |
| 001–096 | close-up رأسي لحافة خشب + strip light ثم reveal عبر فاصل طويل. |
| 097–288 | الصالة: ضع pendant أو عمود travertine في الثلث العلوي، واجعل البوكلي في الثلث السفلي. |
| 289–480 | الجزيرة: كشف رأسي من سطح الترافرتين إلى الإضاءة المعلقة؛ تجنب لقطة أفقية واسعة بلا عنصر طولي. |
| 481–672 | الممر والنوم: استخدم doorframes والستائر كطبقات عمودية، وعدسة 32–35mm. |
| 673–864 | Hero: rise أبطأ من الأفقي، يبدأ من مستوى أثاث وينتهي عند مستوى pendant/curtain line. |

## الخامات — acceptance checks

- **Bouclé:** sheen حقيقي، roughness 0.75–0.85 متغير، micro displacement محدود؛ SSS = 0.
- **Walnut/Rosewood:** اتجاه عروق مختلف لكل لوح، color variance خفيف، pores دقيقة، bevel حقيقي لكل حافة مرئية.
- **Travertine:** pores/veins على مقياس معماري واقعي، roughness غير منتظم، لا normal مبالغ.
- **Brushed bronze:** metallic 1.0، roughness اتجاهي وفق اتجاه السحب/الدوران، لا scratches مرئية كضوضاء.
- **Greige plaster:** bump هادئ جداً يكسر الانعكاس ولا يظهر كنمط texture.

## مراجعات إلزامية

1. **Path preview:** 1/4 resolution، بلا denoise، فقط لاكتشاف clipping والسرعة.
2. **Material check:** 6 stills ممثلة، مع crop 100% للبوكلي/الحجر/المعدن.
3. **Lighting check:** تحقق من detail داخل النوافذ ومن عدم سحق الظلال.
4. **Final conform:** تحقق من markers ومن عدم إسراع الحركة في نسخة 9:16؛ صدّر ProRes/DNxHR master قبل H.264/H.265 delivery.
