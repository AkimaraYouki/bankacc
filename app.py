
import os
from typing import Tuple

import pandas as pd
import streamlit as st

# ===================== 데이터 로드 =====================
def load_proc() -> Tuple[pd.DataFrame, pd.DataFrame]:

    try:
        import asd
    except Exception as e:
        st.error(f"asd.py를 import할 수 없습니다: {e}")
        st.stop()

    # 함수 호출 (인자 유무 호환)
    try:
        proc = asd.load_and_process(os.environ.get("BANK_CSV", "bank.csv"))
    except TypeError:
        # 인자를 받지 않는 구버전
        proc = asd.load_and_process()

    # 반환값 정규화
    if isinstance(proc, dict):
        if "df" not in proc or "daily" not in proc:
            st.error("asd.load_and_process() 결과 dict에 'df' 또는 'daily' 키가 없습니다.")
            st.stop()
        return proc["df"], proc["daily"]

    if isinstance(proc, (list, tuple)):
        if len(proc) < 2:
            st.error("asd.load_and_process() 결과가 (df, daily, ...) 형태가 아닙니다.")
            st.stop()
        return proc[0], proc[1]

    st.error("asd.load_and_process() 결과 타입을 인식할 수 없습니다. dict 또는 (df, daily, ...) 여야 합니다.")
    st.stop()

# ===================== 유틸 =====================
def fmt_money(n: float, signed: bool = False) -> str:
    try:
        n = int(round(float(n)))
    except Exception:
        n = 0
    s = f"{abs(n):,}"
    if not signed:
        return s
    return ("+" if n > 0 else "-" if n < 0 else "") + s

def wrap_label(text: str, width: int = 7) -> str:
    """긴 상호명은 width 글자마다 줄바꿈 삽입"""
    if not text:
        return ""
    text = str(text)
    parts, line = [], []
    for i, ch in enumerate(text, 1):
        line.append(ch)
        if i % width == 0:
            parts.append("".join(line)); line = []
    if line:
        parts.append("".join(line))
    return "\n".join(parts)

# ===================== 페이지/스타일 =====================
st.set_page_config(page_title="일별 거래 대시보드", layout="wide")

st.markdown(
    """
    <style>
      .highlight-box {
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 16px;
        background: rgba(239,68,68,0.1);
        margin-top: 12px;
      }
      .highlight-box h3, .highlight-box h2, .highlight-box b {
        color: #ef4444;
      }
      :root {
        --bg:#0f172a; --border:#1f2937; --card:#111827; --text:#e5e7eb; --muted:#94a3b8;
        --deposit:#ef4444; --withdraw:#3b82f6; --net:#facc15;
      }
      html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
      .box {
        padding:14px 18px; border:1px solid var(--border); border-radius:14px; background:var(--card); color:var(--text);
        box-shadow: 0 2px 8px rgba(15,23,42,0.05);
      }
      .kpi { display:flex; gap:20px; flex-wrap:wrap; margin-top:8px; }
      .kpi .item { min-width: 160px; padding:10px 12px; border:1px solid var(--border); border-radius:12px; background:#1f2937; }
      .kpi .label { display:block; font-size:12px; letter-spacing:.02em; color:var(--muted); margin-bottom:6px; }
      .kpi .value { font-size:20px; font-weight:700; line-height:1.15; }
      .value-deposit { color: var(--deposit); }
      .value-withdraw { color: var(--withdraw); }
      .value-net { color: var(--net); }
      .section-line { border:none; border-top:1px solid var(--border); margin:12px 0; }
      .row-muted { color: var(--muted); font-size:13px; }
      .row-muted b { font-size:15px; font-weight:700; color: var(--text); }
      .title-strong { font-weight:800; font-size:18px; }
      .bigstats { display:flex; gap:16px; margin-top:10px; }
      .bigstats .item { flex:1; padding:18px 20px; border:2px solid var(--border); border-radius:14px; background:#0b1220; }
      .bigstats .item--withdraw { border-color: var(--withdraw); box-shadow: 0 0 0 2px rgba(59,130,246,0.15) inset; }
      .bigstats .item--balance  { border-color: var(--text);    box-shadow: 0 0 0 2px rgba(229,231,235,0.08) inset; }
      .bigstats .label { display:block; font-size:14px; font-weight:700; letter-spacing:.02em; color:var(--muted); margin-bottom:8px; }
      .bigstats .value { font-size:38px; font-weight:900; line-height:1.05; }
      .bigstats .value.value-withdraw { color: var(--withdraw); }
      .bigstats .value.value-balance { color: var(--text); }
      .bigstats .num { font-variant-numeric: tabular-nums; }
      @media (max-width: 900px) {
        .bigstats { flex-direction: column; }
        .bigstats .value { font-size:34px; }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("돈의 행방")

# ===================== 데이터 준비 =====================
df, daily = load_proc()

# 컬럼 표준화
if "date" not in df.columns and "datetime" in df.columns:
    df["date"] = pd.to_datetime(df["datetime"]).dt.date
elif "date" in df.columns:
    df["date"] = pd.to_datetime(df["date"]).dt.date

if not isinstance(daily.index, pd.DatetimeIndex):
    daily.index = pd.to_datetime(daily.index)

available_dates = list(daily.index.date)
if not available_dates:
    st.info("표시할 날짜가 없습니다.")
    st.stop()

# ===================== 날짜 네비게이션 =====================
if "selected_date" not in st.session_state:
    st.session_state.selected_date = available_dates[-1]

cols = st.columns([1,1,2,1,1])
with cols[0]:
    if st.button("◀︎ 이전날"):
        idx = max(0, available_dates.index(st.session_state.selected_date) - 1)
        st.session_state.selected_date = available_dates[idx]
with cols[1]:
    if st.button("오늘"):
        st.session_state.selected_date = available_dates[-1]
with cols[3]:
    if st.button("다음날 ▶︎"):
        idx = min(len(available_dates)-1, available_dates.index(st.session_state.selected_date) + 1)
        st.session_state.selected_date = available_dates[idx]
with cols[2]:
    picked = st.date_input(
        "날짜 선택",
        value=st.session_state.selected_date,
        min_value=available_dates[0],
        max_value=available_dates[-1],
        key="date_input",
    )
    if picked != st.session_state.selected_date:
        st.session_state.selected_date = picked

sel = st.session_state.selected_date
sel_str = str(sel)

# ===================== 요약 박스 (우측) =====================

row = daily.loc[sel_str] if sel_str in daily.index.astype(str) else daily.loc[pd.to_datetime(sel)]

right_col, left_col = st.columns([1,2], gap="large")  # 우측 요약, 좌측 차트/표

with right_col:
    st.markdown(f"<div class='box'><span class='title-strong'>요약 — {sel_str}</span>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='kpi'>
          <div class='item'>
            <span class='label'>입금 (오늘)</span>
            <span class='value value-deposit'>{fmt_money(row.get('deposit', 0))}</span>
          </div>
          <div class='item'>
            <span class='label'>출금 (오늘)</span>
            <span class='value value-withdraw'>{fmt_money(row.get('withdraw', 0))}</span>
          </div>
          <div class='item'>
            <span class='label'>순이익 (오늘)</span>
            <span class='value value-net'>{fmt_money(row.get('net', 0), signed=True)}</span>
          </div>
        </div>
        <hr class='section-line'>
        <div class='bigstats'>
          <div class='item item--withdraw'>
            <span class='label'>현재까지 출금</span>
            <span class='value value-withdraw num'>{fmt_money(row.get('cum_withdraw', 0))}</span>
          </div>
          <div class='item item--balance'>
            <span class='label'>현재까지 재산</span>
            <span class='value value-balance num'>{fmt_money(row.get('last_balance', 0))}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ===================== 차트 + 거래 표 (좌측, 하루) =====================
with left_col:
    day_df = df[df["date"] == sel].copy()
    if "is_internal" in day_df.columns:
        day_df = day_df[~day_df["is_internal"].astype(bool)]
    # 정렬
    day_df = day_df.sort_values("datetime" if "datetime" in day_df.columns else "date")

    st.subheader(f"{sel_str} 거래")
    if day_df.empty:
        st.info("해당 날짜의 거래가 없습니다.")
    else:
        # 당일 거래 표 (차트 제거)
        show_cols = [c for c in ["datetime", "type", "amount", "balance", "category", "counterparty", "memo"] if c in day_df.columns]
        st.dataframe(day_df[show_cols].reset_index(drop=True))


with st.expander("수호가 돈을 쓰는 습관과 문제점"):
    st.markdown(
        """
<div class='highlight-box'>
## 🚨 소비 문제점 — 상세 정리 (중요)

**1) 생활비·연구비 혼합**
- 연구 장비나 대규모 지출이 생활비 계정과 뒤섞여 단기 유동성에 압박을 줌.
- 필요 순간에 일시적으로 큰 금액이 빠져나가면서 일상 소비와 충돌.

**2) 대규모 집중 지출**
- 특정 일자에 고액 결제(예: 네이버페이 장비 구매)가 몰려 예산이 한 번에 흔들림.
- 계획 없이 ‘한 번에 확보’하는 성향이 강해 월 단위 소비 안정성이 약화됨.

**3) 소액 다발 결제**
- 이마트·편의점 등 동일 상호에서 하루평균 3~4번 소비.
- 각 건은 작아도 합산하면 큰 금액 → 지출 체감이 안 되고 파편화.

**4) 교통비 결제 구조**
- 카카오택시 등에서 가승인/환불이 반복 → 실제보다 잔액 변동성이 과장 → 지출파악 힘들어짐.
- 관리 시점마다 금액이 달라져 혼선 발생.

**5) 자동결제의 분산**
- 네이버, 구글, 카카오, LGU+, ChatGPT 등 다양한 플랫폼에서 구독/자동이체 발생.
- 월 고정 지출만 97,000원 
- 고정비가 파편화되어 누락·중복 위험, 총액 파악이 어려움.

**6) 소액 지출 누적 관리 미흡 (3월~6월 특징)**
- 생활/식비에서 계획성 없이 작은 금액들이 자주 사용됨.
- 초반부터 누적되는 ‘눈에 안 보이는 지출’이 후반부 소비 압박으로 이어짐.

**7) 불규칙한 소비 루틴**
- 특정 주간은 거의 소비가 없다가, 다른 주간엔 급증.
- 안정적인 패턴이 없어 계획적 저축/투자가 어려움.

---
**📌 핵심 요약**
- **대규모+소액 반복**이 동시에 존재 → 유동성 관리 취약.
- **자동결제와 교통비 루프**로 실제 재산 흐름이 불투명.
- **생활비·연구비 혼합**으로 예산 통제가 어렵고, 불규칙성으로 계획성이 무너짐.
</div>
        """,
        unsafe_allow_html=True,
    )

# ===================== 고액거래  월 평균 Top5 사용처 탭 =====================
high_tabs = st.tabs(["월 평균 Top5 사용처", "고액거래"])

# 공통: 지출 필터 및 사용처 컬럼 결정
base_df = df.copy()
# 날짜 표준화 보장
if "date" not in base_df.columns and "datetime" in base_df.columns:
    base_df["date"] = pd.to_datetime(base_df["datetime"]).dt.date
elif "date" in base_df.columns:
    base_df["date"] = pd.to_datetime(base_df["date"]).dt.date

# 지출만: type이 있으면 출금, 없으면 amount<0
if "type" in base_df.columns:
    spend_df = base_df[(base_df["type"] == "출금") | (("amount" in base_df.columns) & (base_df["amount"] < 0))].copy()
else:
    spend_df = base_df[base_df["amount"] < 0].copy() if "amount" in base_df.columns else base_df.copy()

# 사용처 컬럼 추론
merchant_col = None
for c in ["merchant", "counterparty", "상대방", "사용처", "desc", "place"]:
    if c in spend_df.columns:
        merchant_col = c; break
if merchant_col is None:
    merchant_col = "_merchant"
    spend_df[merchant_col] = spend_df.get("memo", "미지정")

# 절대 금액 컬럼
if "amount" in spend_df.columns:
    spend_df["abs_amount"] = spend_df["amount"].abs()
else:
    spend_df["abs_amount"] = 0

with high_tabs[0]:
    st.subheader("Top5 사용처 (빈도)")
    # '금오공' 포함 사용처는 하나로 묶어 정규화
    spend_df["_merchant_norm"] = spend_df[merchant_col].astype(str)
    mask = spend_df["_merchant_norm"].str.contains("금오공", na=False)
    spend_df.loc[mask, "_merchant_norm"] = "금오공과대학교 편의점"

    # 사용처별 빈도 계산
    freq_df = spend_df.groupby("_merchant_norm").size().reset_index(name="이용횟수")
    freq_df = freq_df.sort_values("이용횟수", ascending=False).head(5)
    freq_df = freq_df.rename(columns={"_merchant_norm": "사용처(장소)"})
    st.dataframe(freq_df.reset_index(drop=True))


with high_tabs[1]:
    st.subheader("고액거래 목록")
    threshold = st.number_input("기준 금액(>=)", min_value=100000, step=100000, value=100000, format="%d", help="10만원 이상을 기본으로, 10만원 단위로 조정")
    hv = spend_df[spend_df["abs_amount"] >= threshold].copy()
    # 정렬: 금액 내림차순
    hv = hv.sort_values("abs_amount", ascending=False)

    # 표시 컬럼 구성
    disp_cols = []
    for c in ["datetime", "date", merchant_col, "amount", "balance", "category", "memo"]:
        if c in hv.columns and c not in disp_cols:
            disp_cols.append(c)
    if "datetime" not in disp_cols and "date" in hv.columns:
        disp_cols.insert(0, "date")

    # 금액 포맷을 텍스트 컬럼으로 추가(가독성)
    if "amount" in hv.columns:
        hv["금액(원)"] = hv["amount"].astype(int).abs().map(lambda x: f"{x:,}")
        if "amount" in disp_cols:
            disp_cols.remove("amount")
        disp_cols.insert(disp_cols.index(merchant_col)+1 if merchant_col in disp_cols else 1, "금액(원)")

    st.caption(f"총 {len(hv):,}건 | 기준금액: {threshold:,}원")
    st.dataframe(hv[disp_cols].reset_index(drop=True))
# ===================== 문제 해결 가이드 =====================


