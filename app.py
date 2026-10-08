import hashlib
import os
import numpy as np
from PIL import Image, ImageFilter
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
            "score": 88,
            "desc": "도로 중앙부 깊은 함몰 및 음영이 탐지되었습니다.",
            "status": "긴급 조치 필요 ⚠️",
            "process": "접수 완료",
        },
        {
            "id": 2,
            "address": "서울시 중구 세종대로 110",
            "category": "⚡ 도로 균열",
            "score": 62,
            "desc": "도로 표면에 불규칙한 선형 균열 패턴이 감지되었습니다.",
            "status": "주의 진단 🟡",
            "process": "보수 공사 중",
        },
    ]


# 사진별 정밀 동적 위험도 및 유형 판별 알고리즘
def analyze_road_hazard(pil_image):
    # 1. 리사이즈 및 흑백 변환 (표준화)
    img = pil_image.resize((256, 256))
    gray_img = img.convert("L")
    img_np = np.array(gray_img)

    # 2. 도로 하단/중앙 영역 추출 (하늘/배경 배경 노이즈 제거)
    # 이미지 중앙~하단 (y: 30%~90%, x: 15%~85%) 영역만 정밀 분석
    roi = img_np[int(256 * 0.3) : int(256 * 0.9), int(256 * 0.15) : int(256 * 0.85)]

    # 3. 주요 특성 수치 추출
    # A. 짙은 함몰 영역 비율 (포트홀 유무 판단 핵심 - 밝기 50 이하 픽셀)
    deep_dark_pixels = np.sum(roi < 50)
    dark_ratio = (deep_dark_pixels / roi.size) * 100  # 0~100%

    # B. 선형 엣지(균열) 검출 - threshold 적용으로 배경 잔노이즈 제거
    edge_img = gray_img.filter(ImageFilter.FIND_EDGES)
    edge_np = np.array(edge_img)[int(256 * 0.3) : int(256 * 0.9), int(256 * 0.15) : int(256 * 0.85)]
    strong_edges = np.sum(edge_np > 75)
    edge_density = (strong_edges / roi.size) * 100  # 0~100%

    # C. 이미지 해시 기반 고유 변동값 (0~4점 미세조정)
    hash_val = (int(hashlib.md5(gray_img.tobytes()).hexdigest(), 16) % 50) / 10.0

    # 4. 포트홀 vs 균열 분류 및 동적 점수 산출
    # [포트홀 기준]: 짙은 어두운 함몰 영역이 ROI의 4.5% 이상 존재할 때
    if dark_ratio >= 4.5:
        category = "🕳️ 포트홀"
        # 함몰 면적에 비례하여 72점 ~ 96점 분배
        calc_score = 70 + (dark_ratio * 1.8) + hash_val
        score = int(max(72, min(96, calc_score)))
        desc = f"노면 깊은 함몰 및 포트홀 음영이 탐지되었습니다. (함몰 비율: {dark_ratio:.1f}%, 위험도: {score}점)"

    # [도로 균열 기준]: 어두운 구멍은 없으나 뚜렷한 엣지(균열) 밀도가 일정 이상일 때
    elif edge_density >= 1.2:
        category = "⚡ 도로 균열"
        # 균열 밀도에 따라 48점 ~ 84점 범위 내 균등 산출
        calc_score = 45 + (edge_density * 3.5) + hash_val
        score = int(max(48, min(84, calc_score)))
        desc = f"도로 표면 선형 균열 및 틈새 밀도가 탐지되었습니다. (균열 밀도: {edge_density:.1f}%, 위험도: {score}점)"

    # [경미한 요철/일반 상태]
    else:
        category = "🟢 경미한 요철"
        calc_score = 30 + (edge_density * 5.0) + hash_val
        score = int(max(35, min(47, calc_score)))
        desc = f"심각한 파손은 없으나 미세 노후화가 진행 중입니다. (위험도: {score}점)"

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
            with st.spinner("이미지 위험도를 정밀 분석 중입니다..."):
                category, score, desc = analyze_road_hazard(uploaded_image)

                if score >= 75:
                    status = "긴급 조치 필요 ⚠️"
                elif score >= 50:
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
                st.success(f"분석 완료: [{category}] 위험도 {score}점으로 정밀 진단되었습니다!")
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
                else ("warning" if r["score"] >= 50 else "normal")
            )
            badge_class = (
                "badge-urgent"
                if r["score"] >= 75
                else ("badge-warning" if r["score"] >= 50 else "badge-normal")
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