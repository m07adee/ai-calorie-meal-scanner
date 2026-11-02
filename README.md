# 🍽️ ماسح السعرات والوجبات الذكي (AI Calorie & Meal Scanner)

تطبيق ويب خفيف بـ **Streamlit** يستقبل صورة وجبة، ويستخدم **Google Gemini** للتعرف على الأكل وتقدير وزنه وحساب السعرات والبروتين والكربوهيدرات والدهون، مع نصائح صحية سريعة.

## المزايا
- رفع صور JPG / PNG / WebP مع عرض فوري ومؤشر تقدم أثناء التحليل.
- مخرجات JSON صارمة عبر مخطط **Pydantic** يُمرَّر لـ Gemini كـ `response_schema`.
- لوحة نتائج: مقاييس رئيسية، توزيع الطاقة، جدول المكونات، ونصائح.
- معالجة أخطاء واضحة: صورة ليست طعاماً، مفتاح مفقود/غير صالح، تجاوز الحصة، انقطاع الاتصال.
- حفظ النتيجة لكل صورة في الجلسة لتجنب استدعاءات API مكررة.

## هيكل المشروع
| الملف | الدور |
|---|---|
| `app.py` | واجهة Streamlit ولوحة النتائج |
| `ai_service.py` | الاتصال بـ Gemini، معالجة الصورة، نماذج Pydantic (`MealAnalysis`, `FoodItem`) |
| `graphify-out/` | خريطة المعرفة للمشروع (Graphify) |
| `requirements.txt` | المكتبات المطلوبة |
| `.env.example` | نموذج متغيرات البيئة |

تدفق البيانات: `app.py` ← `analyze_meal()` ← `load_image()` + Gemini ← `MealAnalysis` (Pydantic) ← `render_results()`.

## التشغيل
```bash
python -m venv .venv
.venv\Scripts\activate          # على Windows
pip install -r requirements.txt
copy .env.example .env          # ثم ضع مفتاحك في GEMINI_API_KEY
streamlit run app.py
```
احصل على المفتاح من [Google AI Studio](https://aistudio.google.com/apikey).

## خريطة المعرفة (Graphify)
بعد أي تعديل على الكود حدّث الخريطة (تحليل AST محلي بدون تكلفة API):
```bash
graphify update .
```
ثم يمكن الاستعلام عنها:
```bash
graphify query "كيف تصل نتيجة Gemini إلى الواجهة؟"
graphify path "app.py" "MealAnalysis"
```
وافتح `graphify-out/graph.html` لعرض الخريطة تفاعلياً.

> ⚠️ القيم تقديرية بالاعتماد على الصورة فقط، ولا تغني عن استشارة مختص تغذية.
