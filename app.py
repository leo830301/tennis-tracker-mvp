import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

st.set_page_config(page_title="Tennis Tracker MVP", page_icon="🎾", layout="wide")


@st.cache_resource
def get_engine():
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"],
        port=int(st.secrets["DB_PORT"]),
        database=st.secrets["DB_NAME"],
    )
    return create_engine(db_url, pool_pre_ping=True)

engine = get_engine()


def run_query(query, params=None):
    with engine.connect() as conn:
        if params:
            return pd.read_sql(text(query), conn, params=params)
        return pd.read_sql(text(query), conn)


def execute_insert(sql, params):
    with engine.begin() as conn:
        conn.execute(text(sql), params)


def metric_win_rate(df):
    if df.empty or "result" not in df.columns:
        return "-"
    wins = (df["result"] == "승").sum()
    return f"{wins / len(df) * 100:.1f}%"


def render_sidebar():
    st.sidebar.title("🎾 Tennis Tracker MVP")
    st.sidebar.caption("복식 경기 기록 + 레슨 기록 관리용 Streamlit MVP")

    page = st.sidebar.radio(
        "메뉴",
        ["홈", "경기 기록 입력", "레슨 기록 입력", "저널 입력", "기록 조회", "AI 코치 준비"],
    )

    st.sidebar.divider()
    st.sidebar.markdown("**현재 저장 구조**")
    st.sidebar.markdown("- Supabase Postgres 저장\n- 경기/레슨/저널 입력\n- 최근 기록 조회\n- AI 확장용 데이터 구조")
    return page


def home_page(matches_df, lessons_df, journal_df):
    st.title("아마추어 테니스 기록 관리")
    st.write("복식 경기, 레슨, 컨디션 메모를 한곳에 저장하고 이후 AI 코치 기능으로 확장하기 위한 MVP입니다.")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("총 경기 수", len(matches_df))
    c2.metric("승률", metric_win_rate(matches_df))
    c3.metric("총 레슨 수", len(lessons_df))
    c4.metric("저널 수", len(journal_df))

    st.subheader("최근 5경기")
    if matches_df.empty:
        st.info("아직 경기 기록이 없습니다.")
    else:
        cols = [
            "match_date",
            "partner_name",
            "court_position1",
            "score_summary",
            "result",
            "biggest_issue",
            "next_focus",
        ]
        available_cols = [c for c in cols if c in matches_df.columns]
        st.dataframe(matches_df[available_cols].head(5), use_container_width=True, hide_index=True)

    st.subheader("최근 5회 레슨")
    if lessons_df.empty:
        st.info("아직 레슨 기록이 없습니다.")
    else:
        cols = ["lesson_date", "coach_name", "topic", "correction_points", "homework"]
        available_cols = [c for c in cols if c in lessons_df.columns]
        st.dataframe(lessons_df[available_cols].head(5), use_container_width=True, hide_index=True)


def match_form_page():
    st.title("경기 기록 입력")

    with st.form("match_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            match_date = st.date_input("경기일", value=date.today())
            match_type = st.selectbox("경기 유형", ["남복", "여복", "혼복", "기타"])
            venue = st.text_input("장소")
            event_name = st.text_input("이벤트/모임명")
            partner_name = st.text_input("파트너 이름")
            court_position1 = st.selectbox("복식에서 내 위치", ["듀스", "애드"])
            opponent_1 = st.text_input("상대 1")
            opponent_2 = st.text_input("상대 2")
            court_position2 = st.selectbox("복식에서 상대1 위치", ["듀스", "애드"])
            score_summary = st.text_input("스코어", placeholder="예: 6-4 3-6 10-7")
            result = st.selectbox("결과", ["승", "패", "무"])

        with col2:
            serve_rating = st.slider("서브", 1, 10, 5)
            return_rating = st.slider("리턴", 1, 10, 5)
            volley_rating = st.slider("발리", 1, 10, 5)
            positioning_rating = st.slider("포지셔닝", 1, 10, 5)
            communication_rating = st.slider("파트너 커뮤니케이션", 1, 10, 5)
            fitness_rating = st.slider("체력", 1, 10, 5)
            confidence_rating = st.slider("자신감", 1, 10, 5)

        strongest_point = st.text_area("잘한 점")
        biggest_issue = st.text_area("가장 아쉬웠던 점")
        next_focus = st.text_area("다음 경기 집중 포인트")
        notes = st.text_area("추가 메모")

        submitted = st.form_submit_button("경기 기록 저장")

        if submitted:
            execute_insert(
                """
                INSERT INTO matches (
                    match_date, match_type, venue, event_name, partner_name,
                    court_position1, opponent_1, opponent_2, court_position2,
                    score_summary, result, serve_rating, return_rating, volley_rating, positioning_rating,
                    communication_rating, fitness_rating, confidence_rating, strongest_point,
                    biggest_issue, next_focus, notes
                ) VALUES (
                    :match_date, :match_type, :venue, :event_name, :partner_name,
                    :court_position1, :opponent_1, :opponent_2, :court_position2,
                    :score_summary, :result, :serve_rating, :return_rating, :volley_rating, :positioning_rating,
                    :communication_rating, :fitness_rating, :confidence_rating, :strongest_point,
                    :biggest_issue, :next_focus, :notes
                )
                """,
                {
                    "match_date": match_date,
                    "match_type": match_type,
                    "venue": venue,
                    "event_name": event_name,
                    "partner_name": partner_name,
                    "court_position1": court_position1,
                    "opponent_1": opponent_1,
                    "opponent_2": opponent_2,
                    "court_position2": court_position2,
                    "score_summary": score_summary,
                    "result": result,
                    "serve_rating": serve_rating,
                    "return_rating": return_rating,
                    "volley_rating": volley_rating,
                    "positioning_rating": positioning_rating,
                    "communication_rating": communication_rating,
                    "fitness_rating": fitness_rating,
                    "confidence_rating": confidence_rating,
                    "strongest_point": strongest_point,
                    "biggest_issue": biggest_issue,
                    "next_focus": next_focus,
                    "notes": notes,
                },
            )
            st.success("경기 기록이 저장되었습니다.")
            st.rerun()


def lesson_form_page():
    st.title("레슨 기록 입력")

    with st.form("lesson_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            lesson_date = st.date_input("레슨일", value=date.today())
            coach_name = st.text_input("코치 이름")
            topic = st.text_input("레슨 주제", placeholder="예: 리턴, 전위 개입, 서브 후 첫 볼")
            session_rating = st.slider("레슨 만족도", 1, 10, 5)
            physical_condition = st.selectbox("컨디션", ["좋음", "보통", "나쁨"])

        with col2:
            drill_summary = st.text_area("드릴 요약")
            correction_points = st.text_area("교정 포인트")
            homework = st.text_area("숙제")
            next_check_item = st.text_area("다음 점검 항목")

        notes = st.text_area("추가 메모")
        submitted = st.form_submit_button("레슨 기록 저장")

        if submitted:
            execute_insert(
                """
                INSERT INTO lessons (
                    lesson_date, coach_name, topic, drill_summary, correction_points, homework,
                    next_check_item, session_rating, physical_condition, notes
                ) VALUES (
                    :lesson_date, :coach_name, :topic, :drill_summary, :correction_points, :homework,
                    :next_check_item, :session_rating, :physical_condition, :notes
                )
                """,
                {
                    "lesson_date": lesson_date,
                    "coach_name": coach_name,
                    "topic": topic,
                    "drill_summary": drill_summary,
                    "correction_points": correction_points,
                    "homework": homework,
                    "next_check_item": next_check_item,
                    "session_rating": session_rating,
                    "physical_condition": physical_condition,
                    "notes": notes,
                },
            )
            st.success("레슨 기록이 저장되었습니다.")
            st.rerun()


def journal_form_page():
    st.title("저널 입력")

    with st.form("journal_form", clear_on_submit=True):
        journal_date = st.date_input("날짜", value=date.today())
        entry_type = st.selectbox("유형", ["훈련 메모", "경기 전", "경기 후", "부상/통증", "기타"])
        mood = st.selectbox("기분", ["좋음", "보통", "아쉬움", "집중 안 됨", "의욕적"])
        body_condition = st.selectbox("몸 상태", ["가벼움", "보통", "피곤함", "통증 있음"])
        memo = st.text_area("메모")

        submitted = st.form_submit_button("저널 저장")

        if submitted:
            execute_insert(
                """
                INSERT INTO journal (journal_date, entry_type, mood, body_condition, memo)
                VALUES (:journal_date, :entry_type, :mood, :body_condition, :memo)
                """,
                {
                    "journal_date": journal_date,
                    "entry_type": entry_type,
                    "mood": mood,
                    "body_condition": body_condition,
                    "memo": memo,
                },
            )
            st.success("저널이 저장되었습니다.")
            st.rerun()


def records_page(matches_df, lessons_df, journal_df):
    st.title("기록 조회")
    tab1, tab2, tab3 = st.tabs(["경기", "레슨", "저널"])

    with tab1:
        st.caption("최신 경기부터 표시됩니다.")
        st.dataframe(matches_df, use_container_width=True, hide_index=True)

    with tab2:
        st.caption("최신 레슨부터 표시됩니다.")
        st.dataframe(lessons_df, use_container_width=True, hide_index=True)

    with tab3:
        st.caption("최신 메모부터 표시됩니다.")
        st.dataframe(journal_df, use_container_width=True, hide_index=True)


def ai_ready_page(matches_df, lessons_df, journal_df):
    st.title("AI 코치 준비")
    st.write("이 화면은 다음 단계에서 LLM을 붙이기 위한 프롬프트 베이스를 보여줍니다.")

    recent_matches = matches_df.head(5).to_dict(orient="records") if not matches_df.empty else []
    recent_lessons = lessons_df.head(3).to_dict(orient="records") if not lessons_df.empty else []
    recent_journal = journal_df.head(3).to_dict(orient="records") if not journal_df.empty else []

    prompt = f"""
당신은 아마추어 복식 테니스 코치다.
아래 경기 기록, 레슨 기록, 저널을 바탕으로 사용자의 최근 패턴을 분석하라.
1) 잘하는 점 3개
2) 반복 약점 3개
3) 다음 1주일 훈련 계획
4) 다음 경기 체크리스트

[최근 경기]
{recent_matches}

[최근 레슨]
{recent_lessons}

[최근 저널]
{recent_journal}
""".strip()

    st.code(prompt, language="markdown")
    st.info("다음 단계에서는 OpenAI API 또는 LangGraph를 붙여 이 프롬프트를 실제 응답으로 연결하면 됩니다.")


def main():
    page = render_sidebar()

    matches_df = run_query("SELECT * FROM matches ORDER BY match_date DESC, id DESC")
    lessons_df = run_query("SELECT * FROM lessons ORDER BY lesson_date DESC, id DESC")
    journal_df = run_query("SELECT * FROM journal ORDER BY journal_date DESC, id DESC")

    if page == "홈":
        home_page(matches_df, lessons_df, journal_df)
    elif page == "경기 기록 입력":
        match_form_page()
    elif page == "레슨 기록 입력":
        lesson_form_page()
    elif page == "저널 입력":
        journal_form_page()
    elif page == "기록 조회":
        records_page(matches_df, lessons_df, journal_df)
    else:
        ai_ready_page(matches_df, lessons_df, journal_df)


if __name__ == "__main__":
    main()
