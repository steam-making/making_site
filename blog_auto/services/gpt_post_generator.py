from openai import OpenAI
from django.conf import settings
import json, re

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        raise ValueError("JSON not found in response")
    return match.group(0)


def generate_blog_post(topic: str, category_label: str):

    system_prompt = """
    당신의 출력은 반드시 JSON ONLY여야 합니다.
    설명/추가 텍스트/코드블록 금지.
    """

    user_prompt = f"""
    다음 요구사항을 모두 충족하는 JSON을 출력하세요:

    {{
      "titles": [5개 제목],
      "keywords": [10~20개 키워드],
      "content": "2500~3000자 본문",
      "cta": "CTA 문장"
    }}

    주제: {topic}
    카테고리: {category_label}

    ⚠️ JSON 외의 텍스트 절대 출력 금지
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.8,
    )

    raw_text = response.choices[0].message.content

    # JSON 정제
    clean_json = extract_json(raw_text)

    data = json.loads(clean_json)

    return data
