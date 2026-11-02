"""واجهة Streamlit الرئيسية لتطبيق تحليل السعرات والوجبات.

التشغيل:
    streamlit run app.py
"""

from __future__ import annotations

import hashlib

import streamlit as st

from ai_service import MealAnalysis, MealAnalysisError, analyze_meal

SUPPORTED_TYPES = ["jpg", "jpeg", "png", "webp"]

# سعرات كل غرام من العناصر الكبرى (لحساب توزيع الطاقة)
KCAL_PER_GRAM = {"protein": 4, "carbs": 4, "fat": 9}

st.set_page_config(page_title="ماسح السعرات الذكي", page_icon="🍽️", layout="wide")

# اتجاه من اليمين لليسار لعرض العربية بشكل صحيح
st.markdown(
    """
    <style>
    .stApp, .stMarkdown, .stMetric, [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    [data-testid="stMetricValue"] { direction: ltr; text-align: right; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# مكونات العرض
# ---------------------------------------------------------------------------
def render_results(result: MealAnalysis) -> None:
    """عرض لوحة النتائج: المقاييس الرئيسية، توزيع الطاقة، المكونات، والنصائح."""
    st.subheader(f"🍽️ {result.meal_name}")
    st.caption(f"درجة ثقة التقدير: {result.confidence:.0%}")
    if result.confidence < 0.5:
        st.warning("الثقة منخفضة؛ جرّب صورة أوضح من الأعلى وبإضاءة جيدة للحصول على تقدير أدق.")

    # المقاييس الرئيسية
    col1, col2 = st.columns(2)
    col1.metric("🔥 السعرات", f"{result.total_calories:.0f} kcal")
    col2.metric("⚖️ الوزن التقديري", f"{result.estimated_weight_g:.0f} g")

    col3, col4, col5 = st.columns(3)
    col3.metric("🥩 بروتين", f"{result.protein_g:.1f} g")
    col4.metric("🍞 كربوهيدرات", f"{result.carbs_g:.1f} g")
    col5.metric("🧈 دهون", f"{result.fat_g:.1f} g")

    # توزيع الطاقة بين العناصر الكبرى
    macro_kcal = {
        "البروتين": result.protein_g * KCAL_PER_GRAM["protein"],
        "الكربوهيدرات": result.carbs_g * KCAL_PER_GRAM["carbs"],
        "الدهون": result.fat_g * KCAL_PER_GRAM["fat"],
    }
    total_macro_kcal = sum(macro_kcal.values())
    if total_macro_kcal > 0:
        with st.container(border=True):
            st.markdown("**توزيع الطاقة**")
            for label, kcal in macro_kcal.items():
                share = kcal / total_macro_kcal
                st.progress(share, text=f"{label}: {share:.0%}")

    # تفاصيل المكونات
    if result.items:
        with st.expander("🥗 المكونات المكتشفة", expanded=True):
            st.dataframe(
                [
                    {
                        "المكوّن": item.name,
                        "الوزن (g)": round(item.estimated_weight_g),
                        "السعرات (kcal)": round(item.calories),
                    }
                    for item in result.items
                ],
                hide_index=True,
            )

    # النصائح الصحية
    if result.health_tips:
        with st.container(border=True):
            st.markdown("**💡 نصائح صحية**")
            for tip in result.health_tips:
                st.markdown(f"- {tip}")


# ---------------------------------------------------------------------------
# الصفحة الرئيسية
# ---------------------------------------------------------------------------
def main() -> None:
    st.title("🍽️ ماسح السعرات والوجبات الذكي")
    st.write("ارفع صورة لوجبتك وسيقوم الذكاء الاصطناعي بالتعرف عليها وتقدير سعراتها وعناصرها الغذائية.")

    with st.sidebar:
        st.header("ℹ️ نصائح للتصوير")
        st.markdown(
            "- صوّر الطبق من الأعلى أو بزاوية مائلة قليلاً.\n"
            "- استخدم إضاءة جيدة.\n"
            "- أظهر أداة مرجعية (ملعقة، شوكة) لتقدير الحجم.\n"
            "- النتائج تقديرية ولا تغني عن استشارة مختص تغذية."
        )

    uploaded = st.file_uploader("اختر صورة الوجبة", type=SUPPORTED_TYPES)
    if uploaded is None:
        st.info("⬆️ ابدأ برفع صورة بصيغة JPG أو PNG أو WebP.")
        return

    image_bytes = uploaded.getvalue()
    # مفتاح فريد للصورة لحفظ النتيجة وعدم إعادة استدعاء API عند كل إعادة تشغيل للصفحة
    image_key = hashlib.sha256(image_bytes).hexdigest()
    cache: dict[str, MealAnalysis] = st.session_state.setdefault("results", {})

    image_col, result_col = st.columns([2, 3], gap="large")

    with image_col:
        st.image(image_bytes, caption=uploaded.name)
        analyze_clicked = st.button("🔍 حلّل الوجبة", type="primary", width="stretch")

    with result_col:
        if analyze_clicked and image_key not in cache:
            with st.status("جارٍ تحليل الوجبة...", expanded=True) as status:
                st.write("📤 إرسال الصورة إلى Gemini...")
                try:
                    result = analyze_meal(image_bytes)
                except MealAnalysisError as exc:
                    status.update(label="فشل التحليل", state="error")
                    st.error(str(exc))
                    return
                st.write("🧮 حساب العناصر الغذائية...")
                status.update(label="اكتمل التحليل", state="complete", expanded=False)
            cache[image_key] = result

        result = cache.get(image_key)
        if result is None:
            st.info("اضغط على زر «حلّل الوجبة» لبدء التحليل.")
        elif not result.is_food:
            st.error(f"🚫 لا يبدو أن الصورة تحتوي على طعام ({result.meal_name}). جرّب صورة وجبة.")
        else:
            render_results(result)


if __name__ == "__main__":
    main()
