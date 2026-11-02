import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── 기본 설정 ────────────────────────────────────────────────────
APP_TITLE = "뇌졸중 예측 실습실"
APP_ICON = "🧠"

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

DATA_URL = (
    "https://raw.githubusercontent.com/wkd0009/data/refs/heads/main/stroke.csv"
)

COLOR_NO = "#4C78A8"    # 뇌졸중 아님: 파랑
COLOR_YES = "#E45756"   # 뇌졸중: 빨강
COLOR_HIST = "#72B7B2"
GROUPS = [(0, "뇌졸중 아님", COLOR_NO), (1, "뇌졸중", COLOR_YES)]


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_URL, encoding="utf-8")


def ratio(part: int, whole: int) -> float:
    return part / whole * 100 if whole else 0.0


# ── 화면 맨 위 ───────────────────────────────────────────────────
st.title(f"{APP_ICON} {APP_TITLE}")
st.header("탐색")

try:
    df = load_data()
except Exception as e:  # 인터넷 연결 문제 등
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

st.caption(f"전체 {len(df):,}명의 데이터를 살펴봐요. stroke가 1이면 뇌졸중, 0이면 아님이에요.")

# ── 1. 나이와 평균 혈당의 분포 (히스토그램 두 개) ────────────────
st.subheader("나이와 평균 혈당의 분포")


def histogram(col: str, label: str) -> go.Figure:
    fig = go.Figure(
        go.Histogram(x=df[col], nbinsx=30, marker_color=COLOR_HIST,
                     marker_line=dict(width=0.5, color="white"))
    )
    fig.update_layout(
        xaxis_title=label, yaxis_title="사람 수", bargap=0.03,
        height=380, margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


h1, h2 = st.columns(2)
h1.markdown("**나이**")
h1.plotly_chart(histogram("age", "나이"), width="stretch")
h2.markdown("**평균 혈당**")
h2.plotly_chart(histogram("avg_glucose_level", "평균 혈당"), width="stretch")

# ── 2. 뇌졸중 여부별 상자그림 + 평균값 표 ────────────────────────
st.subheader("뇌졸중을 겪은 사람과 겪지 않은 사람 비교")


def boxplot(col: str, label: str) -> go.Figure:
    fig = go.Figure()
    for val, name, color in GROUPS:
        fig.add_trace(
            go.Box(y=df.loc[df["stroke"] == val, col], name=name,
                   marker_color=color, boxmean=True)
        )
    fig.update_layout(
        yaxis_title=label, showlegend=False,
        height=420, margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


b1, b2 = st.columns(2)
b1.markdown("**나이**")
b1.plotly_chart(boxplot("age", "나이"), width="stretch")
b2.markdown("**평균 혈당**")
b2.plotly_chart(boxplot("avg_glucose_level", "평균 혈당"), width="stretch")
st.caption("상자 안의 굵은 선은 가운데 값(중앙값), 점선은 평균값이에요.")

rows = []
for val, name, _ in GROUPS:
    sub = df[df["stroke"] == val]
    rows.append(
        {
            "구분": name,
            "사람 수": f"{len(sub):,}명",
            "나이 평균값": round(float(sub["age"].mean()), 1),
            "평균 혈당 평균값": round(float(sub["avg_glucose_level"].mean()), 1),
        }
    )
st.markdown("**두 그룹의 평균값**")
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

# ── 3. 고혈압·심장병 유무별 뇌졸중 비율 (막대그래프) ──────────────
st.subheader("고혈압·심장병이 있는 사람과 없는 사람의 뇌졸중 비율")


def stroke_rate_by(col: str) -> tuple:
    """값(0/1)별로 이름, 뇌졸중 비율, 막대 글자를 만든다."""
    names, rates, texts = [], [], []
    for val in sorted(df[col].dropna().unique()):
        sub = df[df[col] == val]
        n_stroke = int((sub["stroke"] == 1).sum())
        r = ratio(n_stroke, len(sub))
        names.append("있음" if val == 1 else "없음")
        rates.append(r)
        texts.append(f"{r:.1f}%<br>({len(sub):,}명 중 {n_stroke:,}명)")
    return names, rates, texts


def rate_bar(label: str, data: tuple, y_max: float) -> go.Figure:
    names, rates, texts = data
    fig = go.Figure(
        go.Bar(
            x=names, y=rates, text=texts, textposition="outside",
            marker_color=["#9aa5b1" if n == "없음" else "#F58518" for n in names],
            hovertemplate="%{x}: %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title=label, yaxis_title="뇌졸중 비율 (%)",
        yaxis=dict(range=[0, y_max]),
        height=420, margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


hyper = stroke_rate_by("hypertension")
heart = stroke_rate_by("heart_disease")
y_max = max(hyper[1] + heart[1] + [1.0]) * 1.35  # 두 그림의 세로 눈금을 같게

r1, r2 = st.columns(2)
r1.markdown("**고혈압**")
r1.plotly_chart(rate_bar("고혈압", hyper, y_max), width="stretch")
r2.markdown("**심장병**")
r2.plotly_chart(rate_bar("심장병", heart, y_max), width="stretch")

# ── 4. 체질량지수(bmi)가 빈 사람들의 뇌졸중 비율 ─────────────────
st.subheader("체질량지수(bmi)가 비어 있는 사람들")
missing = df[df["bmi"].isna()]
bmi_rows = []
for name, sub in [("체질량지수(bmi)가 빈 사람", missing), ("전체", df)]:
    n_stroke = int((sub["stroke"] == 1).sum())
    bmi_rows.append(
        {
            "구분": name,
            "사람 수": f"{len(sub):,}명",
            "뇌졸중 사람 수": f"{n_stroke:,}명",
            "뇌졸중 비율": f"{ratio(n_stroke, len(sub)):.1f}%",
        }
    )
st.dataframe(pd.DataFrame(bmi_rows), hide_index=True, width="stretch")

# ── 5. 흡연 상태의 값마다 사람 수 ────────────────────────────────
st.subheader("흡연 상태(smoking_status)의 값마다 사람 수")
smoking = (
    df["smoking_status"]
    .value_counts(dropna=False)
    .rename_axis("흡연 상태(값)")
    .reset_index(name="사람 수")
)
st.dataframe(smoking, hide_index=True, width="stretch")
