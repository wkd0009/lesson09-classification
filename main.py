import json
from pathlib import Path

import pandas as pd
import streamlit as st

# ── 기본 설정 (브라우저 탭 제목과 아이콘) ─────────────────────────
APP_TITLE = "뇌졸중 예측 실습실"
APP_ICON = "🧠"

st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

DATA_URL = (
    "https://raw.githubusercontent.com/wkd0009/data/refs/heads/main/stroke.csv"
)
RECORD_DIR = Path(__file__).parent / "내_기록"
RECORD_FILE = RECORD_DIR / "기록.json"


# ── 데이터 불러오기 ──────────────────────────────────────────────
@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_URL, encoding="utf-8")


def describe_values(s: pd.Series) -> str:
    """열에 들어 있는 값의 종류를 글로 설명한다."""
    n = s.nunique(dropna=True)
    if n <= 6:
        vals = ", ".join(str(v) for v in sorted(s.dropna().unique(), key=str))
        return f"{n}가지: {vals}"
    if pd.api.types.is_numeric_dtype(s):
        return f"{n}가지 (숫자 {s.min():g} ~ {s.max():g})"
    return f"{n}가지"


# ── 내 기록 불러오기 / 저장하기 ──────────────────────────────────
def load_record() -> dict:
    try:
        with open(RECORD_FILE, encoding="utf-8") as f:
            data = json.load(f)
        meaning = data.get("우리말뜻", {})
        source = data.get("출처", "")
        if isinstance(meaning, dict) and isinstance(source, str):
            return {"우리말뜻": meaning, "출처": source}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return {"우리말뜻": {}, "출처": ""}


def save_record(record: dict) -> None:
    RECORD_DIR.mkdir(exist_ok=True)
    with open(RECORD_FILE, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)


# ── 화면 맨 위: 제목 ─────────────────────────────────────────────
st.title(f"{APP_ICON} {APP_TITLE}")
st.caption("첫 화면: 이 데이터가 무엇인지 알아봐요.")

try:
    df = load_data()
except Exception as e:  # 인터넷 연결 문제 등
    st.error(f"데이터를 불러오지 못했어요: {e}")
    st.stop()

saved = load_record()
saved_meaning = {c: saved["우리말뜻"].get(c, "") for c in df.columns}

# ── 1. 큰 숫자 카드 네 개 ────────────────────────────────────────
st.markdown(
    """
    <style>
    .big-card {
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 14px;
        padding: 22px 12px;
        text-align: center;
        background: rgba(128, 128, 128, 0.08);
    }
    .big-card .num { font-size: 2.8rem; font-weight: 800; line-height: 1.2; }
    .big-card .label { font-size: 1rem; opacity: 0.75; margin-top: 4px; }
    </style>
    """,
    unsafe_allow_html=True,
)

total = len(df)
n_cols = df.shape[1]
n_stroke = int((df["stroke"] == 1).sum())
ratio = n_stroke / total * 100 if total else 0

cards = [
    ("전체 사람 수", f"{total:,}명"),
    ("열 개수", f"{n_cols}개"),
    ("stroke가 1인 사람 수", f"{n_stroke:,}명"),
    ("stroke가 1인 비율", f"{ratio:.1f}%"),
]
for col, (label, value) in zip(st.columns(4), cards):
    col.markdown(
        f'<div class="big-card"><div class="num">{value}</div>'
        f'<div class="label">{label}</div></div>',
        unsafe_allow_html=True,
    )

# ── 2. 열 설명 표 (우리말 뜻 칸만 직접 입력) ─────────────────────
st.subheader("열 설명 표")
st.caption(
    "‘우리말 뜻’ 칸을 눌러 교재를 보고 직접 적어 보세요. "
    "적은 내용은 자동으로 저장되고, 새로고침해도 다시 불러와요."
)

if "base_table" not in st.session_state:
    st.session_state["base_table"] = pd.DataFrame(
        {
            "열 이름": df.columns,
            "우리말 뜻": [saved_meaning[c] for c in df.columns],
            "값의 종류": [describe_values(df[c]) for c in df.columns],
            "빈 값 개수": df.isna().sum().astype(int).values,
        }
    )

edited = st.data_editor(
    st.session_state["base_table"],
    key="column_table",
    hide_index=True,
    width="stretch",
    disabled=["열 이름", "값의 종류", "빈 값 개수"],
    column_config={
        "우리말 뜻": st.column_config.TextColumn(
            "우리말 뜻", help="교재를 보고 직접 적어 넣는 칸이에요.", max_chars=100
        ),
    },
)

# ── 3. 데이터 처음 다섯 줄 ───────────────────────────────────────
st.subheader("데이터 처음 다섯 줄")
st.dataframe(df.head(5), width="stretch")

# ── 4. 데이터 출처 ───────────────────────────────────────────────
st.subheader("데이터 출처")
if "source_text" not in st.session_state:
    st.session_state["source_text"] = saved["출처"]
st.text_area(
    "교재에 나온 출처를 적어 주세요. (입력 후 칸 밖을 누르면 저장돼요)",
    key="source_text",
    height=120,
)

# ── 자동 저장: 바뀐 내용이 있을 때만 json에 쓴다 ─────────────────
new_record = {
    "우리말뜻": {
        row["열 이름"]: (row["우리말 뜻"] or "").strip()
        for _, row in edited.iterrows()
    },
    "출처": st.session_state["source_text"].strip(),
}
if new_record != {"우리말뜻": saved_meaning, "출처": saved["출처"]}:
    save_record(new_record)
    st.toast("내_기록 폴더에 저장했어요.", icon="💾")
