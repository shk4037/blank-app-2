# ...existing code...
import os
from datetime import datetime, date
import pandas as pd
import streamlit as st
import altair as alt

# 설정
st.set_page_config(page_title="EmoRhythm", layout="wide")
DATA_DIR = os.path.join(os.getcwd(), "data")
CSV_PATH = os.path.join(DATA_DIR, "responses.csv")

# 감정 맵핑
emotions = {
    "😄 행복해요": {"category": "positive", "score": 3},
    "🙂 그냥 괜찮아요": {"category": "positive", "score": 2},
    "😐 피곤해요": {"category": "neutral", "score": 1.5},
    "😞 속상해요": {"category": "negative", "score": 1},
    "😡 화가 나요": {"category": "negative", "score": 1}
}

# 미션 텍스트
MISSIONS = {
    "positive_share": {
        "title": "오늘의 감정 나눔 미션 💬",
        "desc": "오늘 좋았던 이유를 친구에게 한 가지씩 이야기해보자. 서로의 이야기에 진심으로 귀 기울여주세요. (예: '오늘 체육시간이 재밌었어')"
    },
    "recharge": {
        "title": "오늘의 회복 미션 ☕",
        "desc": "몸과 마음이 조금 쉬어갈 수 있는 시간을 3분만 갖자. 서로에게 '고마웠던 점' 한 가지를 남겨보자. (예: '수업 준비 도와줘서 고마워')"
    },
    "empathy": {
        "title": "오늘의 공감 미션 🤝",
        "desc": "친구가 힘들어 보이면 조용히 '괜찮아?'라고 한마디 건네주기. 장난식이 아니라 진짜로. (예: '너 괜찮아? 같이 쉬자')"
    }
}

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_csv():
    ensure_data_dir()
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df
    else:
        cols = ["timestamp", "student_name", "emotion_label", "emotion_category", "score", "reason_text"]
        return pd.DataFrame(columns=cols)

def append_to_csv(row: dict):
    ensure_data_dir()
    exists = os.path.exists(CSV_PATH)
    pd.DataFrame([row]).to_csv(CSV_PATH, mode="a", header=not exists, index=False)

def init_session():
    if "df" not in st.session_state:
        st.session_state.df = load_csv()

def add_response(name: str, emotion_label: str, reason: str):
    meta = emotions.get(emotion_label, {"category": "neutral", "score": 1.5})
    ts = datetime.now()
    row = {
        "timestamp": ts.isoformat(),
        "student_name": name,
        "emotion_label": emotion_label,
        "emotion_category": meta["category"],
        "score": meta["score"],
        "reason_text": reason
    }
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([row])], ignore_index=True)
    append_to_csv(row)

def compute_aggregates(df: pd.DataFrame):
    if df is None or df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    counts = df["emotion_label"].value_counts().rename_axis("emotion").reset_index(name="count")
    cat_counts = df["emotion_category"].value_counts().rename_axis("category").reset_index(name="count")
    if not cat_counts.empty:
        cat_counts["pct"] = (cat_counts["count"] / cat_counts["count"].sum()) * 100
    df_loc = df.copy()
    df_loc["timestamp"] = pd.to_datetime(df_loc["timestamp"], errors="coerce")
    df_loc["date"] = df_loc["timestamp"].dt.date
    daily = pd.DataFrame()
    if "score" in df_loc.columns and not df_loc["score"].isnull().all():
        daily = df_loc.groupby("date")["score"].mean().reset_index()
    return counts, cat_counts, daily

def pick_mission(cat_counts: pd.DataFrame):
    if cat_counts is None or cat_counts.empty:
        return MISSIONS["recharge"]
    total = cat_counts["count"].sum()
    if total == 0:
        return MISSIONS["recharge"]
    cat_map = dict(zip(cat_counts["category"], cat_counts["count"]))
    pos_pct = cat_map.get("positive", 0) / total
    neg_pct = cat_map.get("negative", 0) / total
    neutral_pct = cat_map.get("neutral", 0) / total
    if pos_pct >= 0.7:
        return MISSIONS["positive_share"]
    if neg_pct >= 0.4:
        return MISSIONS["empathy"]
    return MISSIONS["recharge"]

def teacher_summary(cat_counts: pd.DataFrame):
    if cat_counts is None or cat_counts.empty:
        return "교사용 제안: 아직 제출된 응답이 없습니다."
    total = cat_counts["count"].sum()
    if total == 0:
        return "교사용 제안: 아직 제출된 응답이 없습니다."
    cat_map = dict(zip(cat_counts["category"], cat_counts["count"]))
    pos = cat_map.get("positive", 0)
    neu = cat_map.get("neutral", 0)
    neg = cat_map.get("negative", 0)
    if neg / total >= 0.4:
        return "교사용 제안: 부정적 감정 비율이 높습니다. 수업 초반에 공감과 안정화 시간을 권장합니다."
    if pos / total >= 0.7:
        return "교사용 제안: 전체적으로 긍정적입니다. 감정 나눔으로 긍정 경험을 확장해보세요."
    if neu / total >= 0.5:
        return "교사용 제안: 중립/피곤 비율이 높습니다. 짧은 회복 시간이나 준비 시간을 고려해보세요."
    return "교사용 제안: 학생들의 감정이 혼재되어 있습니다. 간단한 체크인 후 수업을 진행하세요."

def render_header():
    st.markdown(
        f"<h1 style='color:#6C4CCF; font-size:40px; margin:0'>EmoRhythm</h1>"
        f"<p style='color:#6C4CCF; font-size:18px; margin:0'>감정은 평가되지 않고, 공유된다.</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

def main():
    init_session()
    render_header()

    col1, col2 = st.columns([1, 1.4])

    # -----------------------
    # [섹션 A] 오늘의 감정 입력하기
    # -----------------------
    with col1:
        st.subheader("오늘의 감정 입력하기")
        with st.form("input_form"):
            name = st.text_input("이름(간단한 닉네임 가능)", max_chars=30)
            emotion_label = st.radio("지금 기분을 골라주세요", list(emotions.keys()))
            reason = st.text_area("왜 그렇게 느끼나요? (선택 사항)", height=80)
            submitted = st.form_submit_button("제출")
            if submitted:
                if not name:
                    st.warning("이름(닉네임)을 입력해 주세요.")
                else:
                    add_response(name=name, emotion_label=emotion_label, reason=reason)
                    st.success("기록 완료! 감사합니다.")

    # -----------------------
    # [섹션 B] 우리 반 감정 현황 보기
    # -----------------------
    with col2:
        st.subheader("우리 반 감정 현황")
        df = st.session_state.df.copy()
        counts, cat_counts, daily = compute_aggregates(df)

        total_responses = len(df)
        st.markdown(f"### 현재 응답: {total_responses}명")

        if not counts.empty:
            bar_df = counts.set_index("emotion")
            st.write("감정별 인원 수")
            st.bar_chart(bar_df["count"])

            if not cat_counts.empty:
                pie_df = cat_counts.copy()
                pie_chart = alt.Chart(pie_df).mark_arc(innerRadius=20).encode(
                    theta=alt.Theta(field="count", type="quantitative"),
                    color=alt.Color(field="category", type="nominal",
                                    scale=alt.Scale(domain=["positive", "neutral", "negative"],
                                                    range=["#7B61FF", "#A59BFF", "#FF6B6B"]))
                ).properties(width=250, height=250, title="긍정/중립/부정 비율")
                st.altair_chart(pie_chart, use_container_width=True)

            if not daily.empty:
                daily_chart = alt.Chart(daily).mark_line(point=True).encode(
                    x=alt.X("date:T", title="날짜"),
                    y=alt.Y("score:Q", title="평균 감정 점수")
                ).properties(height=200)
                st.write("날짜별 평균 감정 점수")
                st.altair_chart(daily_chart, use_container_width=True)
        else:
            st.info("아직 제출된 응답이 없습니다. 학생들이 제출하면 통계가 업데이트됩니다.")

    st.markdown("---")

    # -----------------------
    # [섹션 C] 오늘의 감정 미션
    # -----------------------
    st.subheader("오늘의 감정 미션")
    _, cat_counts_for_mission, _ = compute_aggregates(st.session_state.df.copy())
    mission = pick_mission(cat_counts_for_mission)
    with st.container():
        st.markdown(
            f"<div style='border:2px solid #6C4CCF; border-radius:8px; padding:12px'>"
            f"<h3 style='color:#6C4CCF;margin:0'>{mission['title']}</h3>"
            f"<p style='margin:6px 0 0 0'>{mission['desc']}</p>"
            f"<p style='margin:6px 0 0 0; font-size:12px; color:gray'>이 미션은 학급 전체에게 보여주고, 서로 도와주자는 취지입니다.</p>"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # -----------------------
    # [섹션 D] 교사 참고 영역(짧은 문장)
    # -----------------------
    st.subheader("교사용 참고")
    teacher_note = teacher_summary(cat_counts_for_mission)
    st.info(teacher_note)

    st.caption("이 화면은 학급 전체의 감정 분위기만 나타냅니다. 특정 학생을 지목하거나 평가하지 않도록 합니다.")

if __name__ == "__main__":
    main()
    