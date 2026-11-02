"""خدمة الذكاء الاصطناعي: الاتصال بـ Gemini وإرجاع نتائج منظمة عبر Pydantic.

يفصل هذا الملف منطق التحليل عن الواجهة، فلا يعرف شيئاً عن Streamlit.
الواجهة (app.py) تستدعي analyze_meal() فقط وتتعامل مع MealAnalysis أو MealAnalysisError.
"""

from __future__ import annotations

import io
import os

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"

# أقصى بُعد للصورة قبل إرسالها؛ يقلل زمن الرفع والتكلفة دون خسارة تُذكر في الدقة
MAX_IMAGE_SIDE = 1536


# ---------------------------------------------------------------------------
# نماذج البيانات (Pydantic)
# تُمرَّر هذه النماذج إلى Gemini كـ response_schema لإجباره على JSON مطابق.
# تجنبنا القيم الافتراضية والقيود (ge/le) لأن مخطط Gemini لا يدعمها كلها،
# ونطبّق التحقق المنطقي بعد الاستلام في _sanitize().
# ---------------------------------------------------------------------------
class FoodItem(BaseModel):
    """مكوّن واحد ظاهر في الصورة."""

    name: str = Field(description="اسم المكوّن بالعربية")
    estimated_weight_g: float = Field(description="الوزن التقديري بالغرام")
    calories: float = Field(description="السعرات الحرارية لهذا المكوّن (kcal)")


class MealAnalysis(BaseModel):
    """نتيجة تحليل الوجبة كما يُرجعها النموذج."""

    is_food: bool = Field(description="هل الصورة تحتوي على طعام أو شراب فعلاً؟")
    meal_name: str = Field(description="اسم الوجبة بالعربية، أو وصف قصير للصورة إن لم تكن طعاماً")
    estimated_weight_g: float = Field(description="الوزن الإجمالي التقديري للوجبة بالغرام")
    total_calories: float = Field(description="إجمالي السعرات الحرارية (kcal)")
    protein_g: float = Field(description="البروتين بالغرام")
    carbs_g: float = Field(description="الكربوهيدرات بالغرام")
    fat_g: float = Field(description="الدهون بالغرام")
    items: list[FoodItem] = Field(description="المكونات الظاهرة مع تقدير كل منها")
    health_tips: list[str] = Field(description="2 إلى 4 نصائح صحية قصيرة بالعربية")
    confidence: float = Field(description="ثقة النموذج في التقدير من 0 إلى 1")


class MealAnalysisError(Exception):
    """خطأ موجّه للمستخدم برسالة عربية واضحة يمكن عرضها مباشرة."""


# ---------------------------------------------------------------------------
# البرومبت
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """
أنت خبير تغذية محترف. حلّل صورة الوجبة المرفقة بدقة واتبع الخطوات:

1. حدّد إن كانت الصورة تحتوي طعاماً أو شراباً. إن لم تكن كذلك: اجعل is_food = false،
   وضع كل القيم الرقمية 0، واترك items فارغة، وصف محتوى الصورة باختصار في meal_name.
2. تعرّف على كل مكوّن ظاهر في الطبق.
3. قدّر حجم كل مكوّن بالغرام مستعيناً بمراجع بصرية (حجم الطبق، الملعقة، اليد، الكوب).
4. احسب السعرات والعناصر الغذائية اعتماداً على قيم مرجعية معتمدة (مثل USDA)،
   مع مراعاة طريقة الطهي الظاهرة (قلي، شوي، صلصات، زيوت).
5. يجب أن يساوي total_calories تقريباً مجموع سعرات المكونات،
   وأن يتسق مع المعادلة: 4×البروتين + 4×الكربوهيدرات + 9×الدهون.
6. اكتب 2 إلى 4 نصائح صحية قصيرة وعملية تخص هذه الوجبة تحديداً.
7. اجعل confidence منخفضة إن كانت الصورة غير واضحة أو المكونات مخفية.

اكتب كل النصوص باللغة العربية.
""".strip()


# ---------------------------------------------------------------------------
# الدوال المساعدة
# ---------------------------------------------------------------------------
def _get_client() -> genai.Client:
    """إنشاء عميل Gemini من متغير البيئة GEMINI_API_KEY."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        raise MealAnalysisError(
            "لم يتم العثور على مفتاح GEMINI_API_KEY. انسخ ملف .env.example إلى .env وضع مفتاحك."
        )
    return genai.Client(api_key=api_key)


def load_image(image_bytes: bytes) -> Image.Image:
    """فتح الصورة من البايتات، وتحويلها إلى RGB، وتصغيرها إن كانت كبيرة."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise MealAnalysisError("تعذّر قراءة الصورة. تأكد أنها بصيغة JPG أو PNG أو WebP صالحة.") from exc

    # إزالة الشفافية (PNG/WebP) وتوحيد نمط الألوان
    if image.mode != "RGB":
        image = image.convert("RGB")

    image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    return image


def _sanitize(result: MealAnalysis) -> MealAnalysis:
    """تصحيح القيم غير المنطقية (سالبة أو ثقة خارج النطاق) التي قد يُرجعها النموذج."""
    numeric_fields = ("estimated_weight_g", "total_calories", "protein_g", "carbs_g", "fat_g")
    updates = {name: max(0.0, getattr(result, name)) for name in numeric_fields}
    updates["confidence"] = min(1.0, max(0.0, result.confidence))
    return result.model_copy(update=updates)


# ---------------------------------------------------------------------------
# الواجهة العامة
# ---------------------------------------------------------------------------
def analyze_meal(image_bytes: bytes, model: str | None = None) -> MealAnalysis:
    """تحليل صورة وجبة وإرجاع MealAnalysis.

    يرفع MealAnalysisError برسالة عربية عند أي فشل متوقع
    (مفتاح مفقود، صورة تالفة، خطأ اتصال، استجابة غير صالحة).
    """
    image = load_image(image_bytes)
    client = _get_client()
    model_name = model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=[image, ANALYSIS_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MealAnalysis,
                temperature=0.2,  # حرارة منخفضة لتقديرات أكثر ثباتاً
            ),
        )
    except genai_errors.ClientError as exc:
        # أخطاء 4xx: مفتاح غير صالح، تجاوز الحصة، نموذج غير موجود...
        if exc.code == 429:
            raise MealAnalysisError("تم تجاوز حد الطلبات المسموح. انتظر قليلاً ثم حاول مجدداً.") from exc
        if exc.code in (401, 403):
            raise MealAnalysisError("مفتاح Gemini غير صالح أو لا يملك صلاحية. تحقق من GEMINI_API_KEY.") from exc
        raise MealAnalysisError(f"رفض الخادم الطلب ({exc.code}): {exc.message}") from exc
    except genai_errors.ServerError as exc:
        raise MealAnalysisError("خدمة Gemini غير متاحة حالياً. حاول بعد قليل.") from exc
    except Exception as exc:  # أخطاء الشبكة (انقطاع، مهلة) تأتي من طبقة httpx
        raise MealAnalysisError(f"فشل الاتصال بخدمة Gemini: {exc}") from exc

    # المكتبة تحاول التحويل تلقائياً إلى Pydantic عبر response.parsed
    result = response.parsed
    if not isinstance(result, MealAnalysis):
        # خطة بديلة: التحقق اليدوي من النص الخام
        try:
            result = MealAnalysis.model_validate_json(response.text or "")
        except ValidationError as exc:
            raise MealAnalysisError("أرجع النموذج استجابة غير مكتملة. حاول مرة أخرى بصورة أوضح.") from exc

    return _sanitize(result)
