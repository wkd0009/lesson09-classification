import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="탐색 · 뇌졸중 예측 실습실",
    page_icon="🔍",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


def rate_by_group(df, column, name):
    """column(0/1)에 따라 나눈 두 그룹의 뇌졸중 비율(%)을 표로 만든다."""
    result = (
        df.groupby(column)["stroke"]
        .mean()
        .mul(100)
        .rename("뇌졸중 비율(%)")
        .reset_index()
    )
    result[name] = result[column].map({0: "없음", 1: "있음"})
    return result[[name, "뇌졸중 비율(%)"]]


st.title("🔍 탐색")
st.caption("데이터를 그림과 표로 살펴봐요.")

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요. 인터넷 연결을 확인해 주세요. ({e})")
    st.stop()

df = df.copy()
df["뇌졸중 여부"] = df["stroke"].map({0: "겪지 않음", 1: "겪음"})

# ---------------------------------------------------------------
# 1) 나이와 평균 혈당의 분포 (히스토그램 두 개)
# ---------------------------------------------------------------
st.subheader("1. 나이와 평균 혈당의 분포")
left, right = st.columns(2)

with left:
    fig = px.histogram(
        df,
        x="age",
        nbins=30,
        labels={"age": "나이", "count": "사람 수"},
        title="나이 분포",
    )
    fig.update_layout(yaxis_title="사람 수")
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.histogram(
        df,
        x="avg_glucose_level",
        nbins=30,
        labels={"avg_glucose_level": "평균 혈당"},
        title="평균 혈당 분포",
    )
    fig.update_layout(yaxis_title="사람 수")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------
# 2) 뇌졸중 여부에 따른 나이·평균 혈당 비교 (상자그림 두 개 + 평균값 표)
# ---------------------------------------------------------------
st.subheader("2. 뇌졸중을 겪은 사람과 겪지 않은 사람 비교")
order = {"뇌졸중 여부": ["겪지 않음", "겪음"]}
left, right = st.columns(2)

with left:
    fig = px.box(
        df,
        x="뇌졸중 여부",
        y="age",
        color="뇌졸중 여부",
        category_orders=order,
        labels={"age": "나이"},
        title="나이 비교",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    fig = px.box(
        df,
        x="뇌졸중 여부",
        y="avg_glucose_level",
        color="뇌졸중 여부",
        category_orders=order,
        labels={"avg_glucose_level": "평균 혈당"},
        title="평균 혈당 비교",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

mean_table = (
    df.groupby("뇌졸중 여부")[["age", "avg_glucose_level"]]
    .mean()
    .round(1)
    .reindex(["겪지 않음", "겪음"])
    .rename(columns={"age": "나이 평균", "avg_glucose_level": "평균 혈당의 평균"})
    .reset_index()
)
st.write("두 그룹의 평균값")
st.dataframe(mean_table, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------
# 3) 고혈압·심장병 유무별 뇌졸중 비율 (막대그래프)
# ---------------------------------------------------------------
st.subheader("3. 고혈압·심장병 유무별 뇌졸중 비율")
left, right = st.columns(2)

with left:
    hyper = rate_by_group(df, "hypertension", "고혈압")
    fig = px.bar(
        hyper,
        x="고혈압",
        y="뇌졸중 비율(%)",
        color="고혈압",
        text=hyper["뇌졸중 비율(%)"].round(1).astype(str) + "%",
        title="고혈압 유무별 뇌졸중 비율",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with right:
    heart = rate_by_group(df, "heart_disease", "심장병")
    fig = px.bar(
        heart,
        x="심장병",
        y="뇌졸중 비율(%)",
        color="심장병",
        text=heart["뇌졸중 비율(%)"].round(1).astype(str) + "%",
        title="심장병 유무별 뇌졸중 비율",
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------
# 4) bmi가 빈 사람들의 뇌졸중 비율과 전체 비율
# ---------------------------------------------------------------
st.subheader("4. 체질량지수(bmi)가 빈 사람들")
bmi_empty = df[df["bmi"].isna()]

compare = pd.DataFrame(
    {
        "구분": ["bmi가 빈 사람", "전체"],
        "사람 수": [len(bmi_empty), len(df)],
        "뇌졸중 사람 수": [int((bmi_empty["stroke"] == 1).sum()), int((df["stroke"] == 1).sum())],
    }
)
compare["뇌졸중 비율(%)"] = (compare["뇌졸중 사람 수"] / compare["사람 수"] * 100).round(1)
st.dataframe(compare, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------
# 5) 흡연 상태의 값마다 사람 수
# ---------------------------------------------------------------
st.subheader("5. 흡연 상태별 사람 수")
smoking = (
    df["smoking_status"]
    .value_counts(dropna=False)
    .rename_axis("흡연 상태")
    .reset_index(name="사람 수")
)
st.dataframe(smoking, hide_index=True, use_container_width=True)
