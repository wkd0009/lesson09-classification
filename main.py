import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# 기본 설정: 브라우저 탭 제목과 아이콘
# ---------------------------------------------------------------
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/stroke.csv"
SAVE_DIR = Path(__file__).parent / "내_기록"
SAVE_FILE = SAVE_DIR / "기록.json"


# ---------------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


# ---------------------------------------------------------------
# 내_기록 불러오기 / 저장하기
# ---------------------------------------------------------------
def load_record():
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            record = json.load(f)
        meanings = record.get("우리말_뜻", {})
        source = record.get("출처", "")
        if not isinstance(meanings, dict):
            meanings = {}
        if not isinstance(source, str):
            source = ""
        return {"우리말_뜻": meanings, "출처": source}
    except (OSError, ValueError):
        return {"우리말_뜻": {}, "출처": ""}


def save_record(record):
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return True
    except OSError:
        return False


def describe_values(series):
    """열의 '값의 종류'를 글로 만들어 준다."""
    values = series.dropna().unique()
    if len(values) <= 10:
        try:
            values = sorted(values)
        except TypeError:
            pass
        return ", ".join(str(v) for v in values)
    if pd.api.types.is_numeric_dtype(series):
        return f"숫자 ({series.min():g} ~ {series.max():g})"
    return f"글자 ({len(values)}가지)"


# ---------------------------------------------------------------
# 화면 맨 위: 아이콘 + 제목
# ---------------------------------------------------------------
st.title("🧠 뇌졸중 예측 실습실")
st.caption("뇌졸중 데이터를 살펴보는 첫걸음: 이 데이터는 무엇일까요?")

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오지 못했어요. 인터넷 연결을 확인해 주세요. ({e})")
    st.stop()

# 새로고침하면 새 세션이 되므로, 처음 한 번만 저장된 기록을 불러온다.
if "기록_불러옴" not in st.session_state:
    st.session_state["저장된_기록"] = load_record()
    st.session_state["기록_불러옴"] = True

saved = st.session_state["저장된_기록"]

# ---------------------------------------------------------------
# 1) 큰 숫자 카드 네 개
# ---------------------------------------------------------------
total = len(df)
n_cols = df.shape[1]
stroke_n = int((df["stroke"] == 1).sum())
stroke_ratio = stroke_n / total * 100 if total else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.metric("전체 사람 수", f"{total:,}명")
with c2:
    with st.container(border=True):
        st.metric("열 개수", f"{n_cols}개")
with c3:
    with st.container(border=True):
        st.metric("stroke가 1인 사람 수", f"{stroke_n:,}명")
with c4:
    with st.container(border=True):
        st.metric("stroke가 1인 비율", f"{stroke_ratio:.1f}%")

# ---------------------------------------------------------------
# 2) 열 설명 표 (우리말 뜻 칸은 직접 채우기)
# ---------------------------------------------------------------
st.subheader("열 설명 표")
st.write("'우리말 뜻' 칸은 교재를 보고 직접 채워 넣어 보세요. 적은 내용은 자동으로 저장돼요.")

# 편집 표의 시작값은 세션에서 처음 한 번만 만든다.
if "뜻_표_시작값" not in st.session_state:
    st.session_state["뜻_표_시작값"] = pd.DataFrame(
        {
            "열 이름": list(df.columns),
            "우리말 뜻": [saved["우리말_뜻"].get(col, "") for col in df.columns],
            "값의 종류": [describe_values(df[col]) for col in df.columns],
            "빈 값 개수": [int(df[col].isna().sum()) for col in df.columns],
        }
    )

edited = st.data_editor(
    st.session_state["뜻_표_시작값"],
    hide_index=True,
    use_container_width=True,
    disabled=["열 이름", "값의 종류", "빈 값 개수"],
    column_config={
        "우리말 뜻": st.column_config.TextColumn("우리말 뜻", help="교재를 보고 직접 적어 보세요."),
    },
    key="뜻_표",
)

# ---------------------------------------------------------------
# 3) 데이터 처음 다섯 줄
# ---------------------------------------------------------------
st.subheader("데이터 처음 다섯 줄")
st.dataframe(df.head(5), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------
# 4) 데이터 출처
# ---------------------------------------------------------------
st.subheader("데이터 출처")
source_text = st.text_area(
    "교재에 나온 출처를 적어 보세요.",
    value=saved["출처"],
    height=120,
    key="출처_입력",
)

# ---------------------------------------------------------------
# 저장: 내용이 바뀌었을 때만 내_기록 폴더에 json으로 저장
# ---------------------------------------------------------------
new_record = {
    "우리말_뜻": {
        row["열 이름"]: (row["우리말 뜻"] if isinstance(row["우리말 뜻"], str) else "")
        for _, row in edited.iterrows()
    },
    "출처": source_text,
}

if new_record != st.session_state["저장된_기록"]:
    if save_record(new_record):
        st.session_state["저장된_기록"] = new_record
        st.toast("내_기록에 저장했어요.", icon="💾")
    else:
        st.warning("내_기록 폴더에 저장하지 못했어요.")
