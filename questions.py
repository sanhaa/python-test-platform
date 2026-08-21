# -*- coding: utf-8 -*-
"""2026-AI-PD 실습 기초 사전 테스트 문제 은행.

원본: 2026-AI-PD_실습_기초_문제.docx
객관식 7문항 + 주관식(빈칸 채우기) 3문항, 각 10점 / 총 100점.
"""

TITLE = "2026-AI-PD 실습 기초 문제"
SUBTITLE = "코드 실행 없이 문제 풀기"
POINT_PER_QUESTION = 10

QUESTIONS = [
    {
        "id": 1,
        "type": "choice",
        "title": "딕셔너리 .get() 의 기본값",
        "intro": "날씨 도구는 이렇게 생겼다.",
        "code": """fake_data = {
    '서울': '맑음, 기온 22°C',
    '부산': '흐림, 기온 24°C',
}
print(fake_data.get('제주', '제주의 날씨 데이터를 찾을 수 없습니다.'))""",
        "prompt": "출력 결과는?",
        "options": [
            "None",
            "'' (빈 문자열)",
            "제주의 날씨 데이터를 찾을 수 없습니다.",
            "KeyError 발생",
        ],
        "answer": 3,
    },
    {
        "id": 2,
        "type": "choice",
        "title": "문자열·리스트 슬라이싱",
        "intro": "로딩한 문서를 확인할 때 documents[0].page_content[:300] 처럼 앞부분만 잘라 본다. "
                 "같은 문법을 문자열에 적용하면?",
        "code": """s = 'ABCDEFGHIJ'
print(s[:3], s[3:6], s[-2:])""",
        "prompt": "출력 결과는?",
        "options": [
            "ABC DEF IJ",
            "ABC DEFG IJ",
            "ABCD DEF HIJ",
            "ABC EF IJ",
        ],
        "answer": 1,
    },
    {
        "id": 3,
        "type": "choice",
        "title": "중첩 반복문과 언더스코어",
        "intro": "temperature 0과 2를 비교하는 실습 코드의 뼈대다.",
        "code": """for t in (0.0, 2.0):
    print(f'--- temperature={t}')
    for _ in range(5):
        print('호출')""",
        "prompt": "'호출' 은 총 몇 번 출력되는가?",
        "options": ["2번", "5번", "7번", "10번"],
        "answer": 4,
    },
    {
        "id": 4,
        "type": "choice",
        "title": "조건부 표현식(삼항 연산자)",
        "intro": "LLM이 대문자로 답하는 경우까지 감안해 이렇게 쓴다.",
        "code": """answer = 'KO'
lang = 'ko' if 'ko' in answer.lower() else 'en'
print(lang)""",
        "prompt": "출력 결과는?",
        "options": ["ko", "en", "KO", "True"],
        "answer": 1,
    },
    {
        "id": 5,
        "type": "choice",
        "title": "중첩된 딕셔너리·리스트에서 값 꺼내기",
        "intro": "API에서 받은 응답 JSON의 구조가 다음과 같다.",
        "code": """recv_json = {
    'choices': [
        {'message': {'role': 'assistant', 'content': '안녕하세요'}}
    ]
}""",
        "prompt": "'안녕하세요' 를 꺼내는 올바른 식은?",
        "options": [
            "recv_json['choices']['message']['content']",
            "recv_json['choices'][0]['message']['content']",
            "recv_json[0]['choices']['message']['content']",
            "recv_json['content']",
        ],
        "answer": 2,
    },
    {
        "id": 6,
        "type": "choice",
        "title": "range() 의 세 번째 인자와 슬라이싱",
        "intro": "임베딩 API가 한 번에 10개까지만 처리하므로 나눠서 보낸다.",
        "code": """texts = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
BATCH = 3
for i in range(0, len(texts), BATCH):
    print(texts[i:i + BATCH])""",
        "prompt": "출력으로 알맞은 것은?",
        "options": [
            "3줄 — ['a', 'b', 'c'] / ['d', 'e', 'f'] / ['g']",
            "7줄 — 한 글자씩 한 줄에 하나",
            "2줄 — ['a', 'b', 'c'] / ['d', 'e', 'f'] (마지막 'g' 는 버려짐)",
            "3줄 — ['a', 'b', 'c'] / ['c', 'd', 'e'] / ['e', 'f', 'g']",
        ],
        "answer": 1,
    },
    {
        "id": 7,
        "type": "choice",
        "title": "딕셔너리 초기화와 리스트 누적",
        "intro": "대화 기록 저장소를 평범한 딕셔너리로 나타내면 이렇게 된다.",
        "code": """store = {}
if 'messages' not in store:
    store['messages'] = []
store['messages'].append({'role': 'user', 'content': '안녕'})
print(len(store['messages']), store['messages'][0]['role'])""",
        "prompt": "출력 결과는?",
        "options": ["1 user", "1 안녕", "0 user", "KeyError 발생"],
        "answer": 1,
    },
    {
        "id": 8,
        "type": "text",
        "title": "문자열 안에 변수 값 넣기",
        "intro": "",
        "code": """state = {'question': 'RAG란?'}
answer = ____"질문에 답변: {state['question']}"
print(answer)  # 질문에 답변: RAG란?""",
        "prompt": "{} 안의 값이 실제로 치환되게 하려면 따옴표 앞에 붙여야 하는 한 글자는?",
        "placeholder": "한 글자를 입력하세요",
        "answer": "f",
        "accept": ["f"],
    },
    {
        "id": 9,
        "type": "text",
        "title": "흩어진 공백·줄바꿈 정리하기",
        "intro": "PDF에서 뽑은 지저분한 텍스트를 한 줄로 다듬어 출력한다.",
        "code": r"""raw = 'RAG는 문서를\n조각으로\t나눈다'
text = ' '.__________(raw.split())
print(text)  # RAG는 문서를 조각으로 나눈다""",
        "prompt": "빈칸에 들어갈 메서드 이름은?",
        "placeholder": "메서드 이름을 입력하세요",
        "answer": "join",
        "accept": ["join"],
    },
    {
        "id": 10,
        "type": "text",
        "title": "그래프를 실행 가능한 앱으로",
        "intro": "",
        "code": """builder = StateGraph(State)
builder.add_node('chatbot', chatbot_node)
builder.add_edge(START, 'chatbot')
builder.add_edge('chatbot', END)
app = builder.____________()  # ← 빈칸
result = app.invoke({'messages': [HumanMessage(content='안녕')]})""",
        "prompt": "빈 칸에 들어갈, 노드와 엣지를 다 붙인 그래프를 실행 가능한 앱으로 만드는 메서드는? "
                  "(보기에서 골라 쓰시오: compile / build / run / invoke)",
        "placeholder": "compile / build / run / invoke",
        "answer": "compile",
        "accept": ["compile"],
    },
]

QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}
TOTAL_QUESTIONS = len(QUESTIONS)
MAX_SCORE = TOTAL_QUESTIONS * POINT_PER_QUESTION


def normalize_text(value):
    """주관식 답안 정규화: 공백/대소문자/장식 문자를 제거한다.

    'JOIN', ' .join() ', '"join"' 을 모두 'join' 으로 본다.
    """
    if value is None:
        return ""
    text = str(value).strip().lower()
    for ch in ('"', "'", "`", "(", ")", " ", "\t", "\n", ".", "_"):
        text = text.replace(ch, "")
    return text


def is_correct(question, answer):
    """단일 문항의 자동 채점 결과를 돌려준다."""
    if answer is None or str(answer).strip() == "":
        return False
    if question["type"] == "choice":
        try:
            return int(answer) == question["answer"]
        except (TypeError, ValueError):
            return False
    accepted = {normalize_text(a) for a in question.get("accept", [question["answer"]])}
    return normalize_text(answer) in accepted


def answer_label(question, answer):
    """채점표에 보여줄 사람이 읽을 수 있는 답안 문자열."""
    if answer is None or str(answer).strip() == "":
        return "(무응답)"
    if question["type"] == "choice":
        try:
            idx = int(answer)
        except (TypeError, ValueError):
            return str(answer)
        if 1 <= idx <= len(question["options"]):
            return "%d. %s" % (idx, question["options"][idx - 1])
        return str(answer)
    return str(answer)
