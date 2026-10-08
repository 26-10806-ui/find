import os
from PIL import Image, ImageStat
import streamlit as st

# ---------------------------------------------------------
# 1. 화면 설정 및 CSS 연결
# ---------------------------------------------------------
st.set_page_config(
    page_title="도로 위험 요소 관제 장부",
    layout="wide",
)


def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

# 클래식 입력 창 및 버튼 스타일 커스텀
st.markdown(
    """
    <style>
    .stButton > button {
        background-color: #2c221e !important;
        color: #f5eedf !important;
        border: 2px solid #1a1310 !important;
        font-family: 'Gowun Batang', serif !important;
        font-weight: 700 !important;
        border-radius: 0px !important;
        width: 100%;
        padding: 10px 0px !important;
        letter-spacing: 1px;
    }
    .stButton > button:hover {
        background-color: #4a3b32 !important;
        color: #ffffff !important;
    }
    .stTextInput > div > div > input {
        background-color: #f5eedf !important;
        border: 1px solid #b8a88f !important;
        color: #2c221e !important;
        font-family: 'Gowun Batang', serif !important;
        border-radius: 0px !important;
    }
    .stSelectbox > div > div {
        background-color: #f5eedf !important;
        border: 1px solid #b8a88f !important;
        border-radius: 0px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 고서류 헤더
# ---------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">도로 위험 요소 종합 관제 장부</h1>
        <p class="app-subtitle">현장 사진 진단 기록 및 조치 관리 일지</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. 데이터 초기화
# ---------------------------------------------------------
if "reports" not in st.session_state:
    st.session_state.reports = [
        {
            "id": 1,
            "address": "대구광역시 중구 국채보상로 670",
            "category": "노면 파손",
            "score": 85,
            "desc": "노면 함몰 및 깊은 음영 침하 구간이 확인되었습니다.",
            "status": "긴급 조치 필요",
            "process": "접수 완료",
        },
        {
            "id": 2,
            "address": "서울특별시 중구 세종대로 110",
            "category": "도로 균열",
            "score": 60,
            "desc": "표면 선형 균열이 감지되었습니다.",
            "status": "주의 진단",
            "process": "보수 공사 중",
        },
    ]


# 분석 함수
def analyze_road_hazard(pil_image):
    gray_img = pil_image.convert("L")
    stat = ImageStat.Stat(gray_img)

    std_dev = stat.stddev[0]
    pixels = list(gray_img.getdata())
    total_pixels = len(pixels)
    dark_pixels = sum(1 for p in pixels if p < 80)
    dark_ratio = (dark_pixels / total_pixels) * 100

    calculated_score = int((dark_ratio * 1.8) + (std_dev * 0.8) + 30)
    score = max(45, min(95, calculated_score))

    if score >= 75:
        category = "노면 파손"
        desc = f"침하 비율이 높습니다. (어두운 영역: {dark_ratio:.1f}%)"
    elif score >= 55:
        category = "도로 균열"
        desc = f"표면 균열 형태가 감지되었습니다. (어두운 영역: {dark_ratio:.1f}%)"
    else:
        category = "경미한 요철"
        desc = "경미한 노후화 구간입니다."

    return category, score, desc


# ---------------------------------------------------------
# 4. 레이아웃
# ---------------------------------------------------------
left_col, right_col = st.columns([1, 1.2], gap="large")

# ---------------------------------------------------------
# [왼쪽] 접수 양식
# ---------------------------------------------------------
with left_col:
    st.markdown(
        '<div class="section-title">신고 접수 양식</div>',
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "현장 사진 첨부",
        type=["jpg", "jpeg", "png"],
    )

    uploaded_image = None
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file)
        st.image(
            uploaded_image,
            caption="첨부된 현장 사진",
            use_container_width=True,
        )

    address_input = st.text_input(
        "발견 위치",
        placeholder="주소 또는 정밀 위치를 입력하십시오",
    )

    if st.button("사진 분석 및 기록 등록"):
        if uploaded_image is None:
            st.warning("분석할 사진을 첨부하십시오.")
        elif not address_input.strip():
            st.warning("발견 위치를 입력하십시오.")
        else:
            with st.spinner("사진을 정밀 분석 중입니다..."):
                category, score, desc = analyze_road_hazard(uploaded_image)

                if score >= 75:
                    status = "긴급 조치 필요"
                elif score >= 55:
                    status = "주의 진단"
                else:
                    status = "일반 관찰"

                new_report = {
                    "id": len(st.session_state.reports) + 1,
                    "address": address_input,
                    "category": category,
                    "score": score,
                    "desc": desc,
                    "status": status,
                    "process": "접수 완료",
                }

                st.session_state.reports.append(new_report)
                st.success("관제 장부에 정상 기록되었습니다.")
                st.rerun()

# ---------------------------------------------------------
# [오른쪽] 관제 장부
# ---------------------------------------------------------
with right_col:
    st.markdown(
        '<div class="section-title">관제 기록 장부</div>',
        unsafe_allow_html=True,
    )

    search_query = st.text_input(
        "장부 검색",
        placeholder="지역명 또는 위험 유형 검색",
        label_visibility="collapsed",
    ).strip()

    if search_query:
        filtered_reports = [
            r
            for r in reversed(st.session_state.reports)
            if search_query.lower() in r["address"].lower()
            or search_query.lower() in r["category"].lower()
        ]
        st.caption(f"검색된 기록: 총 {len(filtered_reports)}건")
    else:
        filtered_reports = list(reversed(st.session_state.reports))

    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered_reports:
        st.info("해당하는 기록을 찾을 수 없습니다.")
    else:
        for r in filtered_reports:
            card_class = (
                "urgent"
                if r["score"] >= 75
                else ("warning" if r["score"] >= 55 else "normal")
            )
            badge_class = (
                "badge-urgent"
                if r["score"] >= 75
                else ("badge-warning" if r["score"] >= 55 else "badge-normal")
            )

            # 고서류 양식 카드
            st.markdown(
                f"""
                <div class="report-card {card_class}">
                    <div class="card-header-row">
                        <div class="card-category">
                            <span class="badge {badge_class}">{r['process']}</span>
                            {r['category']}
                        </div>
                        <div class="card-score">위험 수치: {r['score']}점</div>
                    </div>
                    <div class="card-meta"><strong>발견 위치</strong> {r['address']}</div>
                    <div class="card-meta"><strong>진단 소견</strong> {r['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            process_options = ["접수 완료", "보수 공사 중", "조치 완료"]
            current_index = (
                process_options.index(r["process"])
                if r["process"] in process_options
                else 0
            )

            selected_status = st.selectbox(
                f"처리 상태 변경 (기록 번호: {r['id']})",
                process_options,
                index=current_index,
                key=f"status_select_{r['id']}",
                label_visibility="collapsed",
            )

            if selected_status != r["process"]:
                r["process"] = selected_status
                st.rerun()

            st.markdown("<div style='margin-bottom: 18px;'></div>", unsafe_allow_html=True)