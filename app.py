import time
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="나는 무슨 빵일까?🍞",
    page_icon="🍞",
    layout="centered",
)

# -----------------------------
# OpenAI Client (Streamlit Cloud)
# -----------------------------
API_KEY = st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=API_KEY) if API_KEY else None

# -----------------------------
# Session State 초기화
# -----------------------------
NUM_QUESTIONS = 5

if "answers" not in st.session_state:
    st.session_state.answers = [None] * NUM_QUESTIONS

if "current_q" not in st.session_state:
    st.session_state.current_q = 0  # 0-index

if "ai_result" not in st.session_state:
    st.session_state.ai_result = ""

if "has_result" not in st.session_state:
    st.session_state.has_result = False

# -----------------------------
# 리셋 함수
# -----------------------------
def reset_test():
    st.session_state.answers = [None] * NUM_QUESTIONS
    st.session_state.current_q = 0
    st.session_state.ai_result = ""
    st.session_state.has_result = False

    # 현재 문항의 radio 위젯 상태도 모두 초기화
    for i in range(NUM_QUESTIONS):
        key = f"q_{i}"
        if key in st.session_state:
            del st.session_state[key]

# -----------------------------
# 클립보드 복사 (JS)
# -----------------------------
def copy_to_clipboard(text: str):
    js_text = repr(text)
    components.html(
        f"""
        <script>
        async function copyText() {{
            try {{
                await navigator.clipboard.writeText({js_text});
            }} catch (err) {{
                console.log("Clipboard copy failed:", err);
            }}
        }}
        copyText();
        </script>
        """,
        height=0,
    )

# -----------------------------
# 빵 유형별 대표 대사 (결과 카드에 추가)
# -----------------------------
BREAD_CATCHPHRASE = {
    "소금빵": "“심플한데 계속 생각나는 게 내 매력이야.”",
    "크루아상": "“겉은 바삭, 속은 말랑… 나 꽤 다채로운 사람임.”",
    "바게트": "“쉽게 친해지진 않지만, 친해지면 오래 가.”",
    "식빵": "“나랑 있으면 일상이 좀 편해질걸?”",
    "베이글": "“나 좀 단단해 보여도, 속은 꽤 따뜻해.”",
    "단팥빵": "“겉보기보다 정 많은 거, 나만 알면 돼.”",
    "치아바타": "“호불호는 갈려도, 맞는 사람한텐 최애야.”",
    "초코소라빵": "“나랑 있으면 심심할 틈은 없어.”",
}

def append_catchphrase(result_text: str) -> str:
    bread_name = None
    for line in result_text.splitlines():
        if "🍞" in line and "빵 유형" in line and ":" in line:
            bread_name = line.split(":", 1)[1].strip()
            bread_name = bread_name.split()[0].strip()
            break

    if bread_name and bread_name in BREAD_CATCHPHRASE:
        phrase_block = f"\n\n**🐣 대표 대사**\n- {BREAD_CATCHPHRASE[bread_name]}"
        return result_text + phrase_block

    return result_text + "\n\n**🐣 대표 대사**\n- “오늘도 빵처럼 포근하게 굴러가는 중…🍞”"

# -----------------------------
# 시스템 프롬프트 (MZ + 궁합 포함)
# -----------------------------
SYSTEM_PROMPT = f"""
너는 MZ 감성 만렙의 '빵 심리학자'야 🍞✨
사용자의 선택을 바탕으로 "나는 무슨 빵일까?" 결과를 재밌고 찰떡 비유로 알려줘.
톤은 가볍고 유쾌하게, 이모지 적극 사용!

반드시 아래 형식으로 출력해:
1. 🍞 당신의 빵 유형: [빵 이름]
2. 🧠 성격 요약: [2-3문장, 빵 비유 필수]
3. 💡 관계 팁: [1-2개]
4. 💞 궁합이 좋은 빵: [빵 이름]
5. 🔎 궁합 이유: [왜 잘 맞는지 1-2문장]

중요:
- 빵 이름은 아래 목록 중에서만 선택해:
  {", ".join(BREAD_CATCHPHRASE.keys())}
- 궁합이 좋은 빵도 위 목록 중에서 선택해.
- 사용자의 답변 패턴을 근거로 설명해.
"""

def build_user_answers_text(answers):
    return ", ".join([f"질문{i+1}: {ans}" for i, ans in enumerate(answers)])

def stream_ai_result(user_text: str):
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        token = getattr(delta, "content", None)
        if token:
            yield token

# -----------------------------
# 질문 데이터 (빵집 상황 기반)
# -----------------------------
questions = [
    {
        "q": "1) 빵집에 들어가자마자 당신의 시선은?",
        "options": [
            "오늘의 신상/베스트 빵 👀",
            "늘 먹던 익숙한 빵 코너",
            "사람들 많이 고른 빵",
            "천천히 한 바퀴 돌며 전체 탐색",
        ],
    },
    {
        "q": "2) 사고 싶은 빵이 딱 하나 남아 있다면?",
        "options": [
            "고민 없이 바로 집는다",
            "괜히 다른 빵도 비교해본다",
            "다른 사람에게 양보할까 잠깐 고민",
            "다음에 와도 되지… 하고 내려놓는다",
        ],
    },
    {
        "q": "3) 직원이 빵을 추천해준다면?",
        "options": [
            "오 추천 좋아요! 그걸로 주세요",
            "참고만 하고 내 취향대로 고른다",
            "왜 추천인지 이유부터 듣는다",
            "괜히 거절 못 하고 추천받은 걸 산다",
        ],
    },
    {
        "q": "4) 줄이 생각보다 길다. 이때 당신은?",
        "options": [
            "상관없음! 기다리는 김에 구경",
            "속으로 조급해지지만 참고 기다림",
            "나중에 올까 고민하다가 나간다",
            "친구랑 같이라면 수다로 버팀",
        ],
    },
    {
        "q": "5) 계산대 앞, 마지막 선택의 순간!",
        "options": [
            "원래 계획한 빵만 산다",
            "하나쯤 더… 충동 추가",
            "누군가 줄 선 사람을 의식해 빠르게 결정",
            "지금 기분에 끌리는 걸 고른다",
        ],
    },
]

# -----------------------------
# UI - Title & Intro
# -----------------------------
st.title("나는 무슨 빵일까🍞? 빵집 선택으로 보는 성격 테스트")
st.markdown(
    """
빵집에서 실제로 겪을 법한 상황에서 **당신의 선택**을 골라보세요 🥐  
AI가 당신의 **성격 & 인간관계 스타일**을  
찰떡같은 **빵 유형 + 궁합 빵 + 대표 대사**로 알려줘요 💞
"""
)

st.divider()

# -----------------------------
# 진행 상태 표시
# -----------------------------
current = st.session_state.current_q
progress = (current) / NUM_QUESTIONS
st.progress(progress, text=f"진행도: {current}/{NUM_QUESTIONS}")

# -----------------------------
# 현재 질문 1개만 표시
# -----------------------------
q_item = questions[current]
st.subheader(f"Q{current + 1}")
selected = st.radio(
    q_item["q"],
    q_item["options"],
    key=f"q_{current}",
    index=None
    if st.session_state.answers[current] is None
    else q_item["options"].index(st.session_state.answers[current]),
)
st.session_state.answers[current] = selected

st.write("")

# -----------------------------
# 네비게이션 버튼 (다음/이전/결과 보기/리셋)
# -----------------------------
nav1, nav2, nav3 = st.columns([1, 1, 1])

with nav1:
    if st.button("다시 테스트하기"):
        reset_test()
        st.rerun()

with nav2:
    if current > 0:
        if st.button("이전"):
            st.session_state.current_q -= 1
            st.rerun()
    else:
        st.button("이전", disabled=True)

with nav3:
    # 마지막 문항이 아니면 "다음", 마지막이면 "결과 보기"
    if current < NUM_QUESTIONS - 1:
        if st.button("다음", type="primary"):
            if st.session_state.answers[current] is None:
                st.warning("답변을 선택해줘! 😆")
            else:
                st.session_state.current_q += 1
                st.rerun()
    else:
        analyze_clicked = st.button("결과 보기", type="primary")
        if analyze_clicked:
            if not API_KEY:
                st.error("Streamlit Cloud Secrets에 OPENAI_API_KEY를 설정해주세요.")
            elif any(a is None for a in st.session_state.answers):
                st.warning("모든 질문에 답해주세요!")
            else:
                st.session_state.ai_result = ""
                st.session_state.has_result = False

                user_text = build_user_answers_text(st.session_state.answers)

                st.divider()
                with st.container(border=True):
                    st.subheader("🥐 빵 굽는 중… 성격 분석 중입니다")
                    placeholder = st.empty()

                    with st.spinner("오븐 예열 중 🔥"):
                        full_text = ""
                        try:
                            for token in stream_ai_result(user_text):
                                full_text += token
                                placeholder.markdown(full_text)
                                time.sleep(0.02)
                            # 대표 대사 추가
                            full_text = append_catchphrase(full_text)

                            st.session_state.ai_result = full_text
                            st.session_state.has_result = True
                        except Exception as e:
                            st.error(f"AI 분석 중 오류: {e}")

# -----------------------------
# 결과 표시 + 공유
# -----------------------------
if st.session_state.has_result and st.session_state.ai_result:
    st.divider()
    with st.container(border=True):
        st.subheader("🍞 당신의 빵 성격 결과")
        st.markdown(st.session_state.ai_result)

        st.divider()

        if st.button("결과 공유하기", use_container_width=True):
            copy_to_clipboard(st.session_state.ai_result)
            st.success("클립보드에 복사했어요! 📋✨")
