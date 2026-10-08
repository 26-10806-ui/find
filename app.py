import os
from PIL import Image, ImageStat
import streamlit as st

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 분리된 CSS 불러오기
# ---------------------------------------------------------
st.set_page_config(
    page_title="스마트 도로 위험요소 관리 시스템",
    page_icon="🚨",
    layout="wide",
)


# style.css 파일 로드 함수
def load_css(file_name):
    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style.css")

# ---------------------------------------------------------
# 2. HTML 헤더 출력
# ---------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1 class="app-title">🚨 스마트 도로 위험요소 신고 & 관제 시스템</h1>
        <p class="app-subtitle">도로 사진을 올리면 AI 알고리즘이 위험도를 분석하여 관리자에게 실시간 전달합니다.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 3. 세션 상태(데이터 저장소) 및 초기화
# ---------------------------------------------------------
if "reports" not in st.session_state:
    st.session_state.reports = [
        {
            "id": 1,
            "address": "대구광역시 중구 국채보상로 670",
            "category": "🕳️ 포트홀",
            "score": 85,
            "desc": "이미지 명암 분석 결과, 도로 노면에 깊은 파손 음영이 감지되었습니다.",
            "status": "긴급 조치 필요 ⚠️",
            "process": "접수 완료",
        },
        {
            "id": 2,
            "address": "서울시 중구 세종대로 110",
            "category": "⚡ 도로 균열",
            "score": 60,
            "desc": "도로 표면에 불규칙한 선형 균열이 감지되었습니다.",
            "status": "주의 진단 🟡",
            "process": "보수 공사 중",
        },
    ]


# PIL 기본 라이브러리로 도로 위험도를 분석하는 함수
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
        category = "🕳️ 포트홀"
        desc = f"분석 결과, 도로 내 어두운 파손 영역 비율이 높습니다. (음영 비율: {dark_ratio:.1f}%)"
    elif score >= 55:
        category = "⚡ 도로 균열"
        desc = f"도로 표면에 불규칙한 균열 및 침하 음영이 감지되었습니다. (음영 비율: {dark_ratio:.1f}%)"
    else:
        category = "🟡 경미한 요철"
        desc = "경미한 노후화가 진행 중인 구간입니다."

    return category, score, desc


# ---------------------------------------------------------
# 4. 레이아웃 분할 (왼쪽: 업로드 / 오른쪽: 리스트 & 검색)
# ---------------------------------------------------------
left_col, right_col = st.columns([1, 1.2], gap="large")

# ---------------------------------------------------------
# [LEFT] 이미지 업로드 및 신고 등록
# ---------------------------------------------------------
with left_col:
    st.markdown("### 📸 도로 위험요소 신고 등록")

    uploaded_file = st.file_uploader(
        "포트홀, 균열 등 도로 위험 사진을 올려주세요",
        type=["jpg", "jpeg", "png"],
    )

    uploaded_image = None
    if uploaded_file is not None:
        uploaded_image = Image.open(uploaded_file)
        st.image(
            uploaded_image,
            caption="업로드한 이미지",
            use_container_width=True,
        )

    address_input = st.text_input(
        "📍 발견 위치 (주소 또는 건물명)",
        placeholder="예: 대구 중구 중앙대로 397 또는 서울시청 앞",
    )

    if st.button(
        "🚀 위험 요소 분석 및 신고 접수",
        use_container_width=True,
        type="primary",
    ):
        if uploaded_image is None:
            st.warning("분석할 도로 위험 사진을 업로드해 주세요.")
        elif not address_input.strip():
            st.warning("위험 지역 위치를 입력해 주세요.")
        else:
            with st.spinner("이미지 위험도를 분석 중입니다..."):
                category, score, desc = analyze_road_hazard(uploaded_image)

                if score >= 75:
                    status = "긴급 조치 필요 ⚠️"
                elif score >= 55:
                    status = "주의 진단 🟡"
                else:
                    status = "일반 관찰 🟢"

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
                st.success("신고가 성공적으로 완료되었습니다!")
                st.rerun()

# ---------------------------------------------------------
# [RIGHT] 키워드 검색 & 관리자 모드 리스트
# ---------------------------------------------------------
with right_col:
    st.markdown("### 🔍 위험 지역 및 카테고리 검색")

    search_query = st.text_input(
        "주소 또는 위험 유형 검색",
        placeholder="예: 대구, 서울, 포트홀, 균열",
        label_visibility="collapsed",
    ).strip()

    # 검색어로 리스트 필터링
    if search_query:
        filtered_reports = [
            r
            for r in reversed(st.session_state.reports)
            if search_query.lower() in r["address"].lower()
            or search_query.lower() in r["category"].lower()
        ]
        st.caption(
            f"🔎 **'{search_query}'** 검색 결과: 총 **{len(filtered_reports)}건**"
        )
    else:
        filtered_reports = list(reversed(st.session_state.reports))

    st.markdown("---")
    st.markdown("### 👷 관리자 모드 (신고 내역 & 상태 변경)")

    if not filtered_reports:
        st.info("검색 조건에 맞는 신고 내역이 없습니다.")
    else:
        for r in filtered_reports:
            # 상태에 따른 CSS 클래스 적용
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

            # HTML 구조를 활용하여 style.css의 클래스 적용
            st.markdown(
                f"""
                <div class="report-card {card_class}">
                    <div class="card-title">
                        <span class="badge {badge_class}">{r['process']}</span> 
                        {r['category']} (위험도 {r['score']}점)
                    </div>
                    <div class="card-meta"><b>📍 위치:</b> {r['address']}</div>
                    <div class="card-meta"><b>📝 AI 진단:</b> {r['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 처리 상태 변경 드롭다운
            process_options = ["접수 완료", "보수 공사 중", "조치 완료"]
            current_index = (
                process_options.index(r["process"])
                if r["process"] in process_options
                else 0
            )

            selected_status = st.selectbox(
                f"🛠️ '{r['address']}' 처리 상태 변경",
                process_options,
                index=current_index,
                key=f"status_select_{r['id']}",
            )

            if selected_status != r["process"]:
                r["process"] = selected_status
                st.rerun()

            st.write("")