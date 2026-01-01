# blog_auto/services/gpt_image_generator.py

import base64
from django.core.files.base import ContentFile
from openai import OpenAI
from django.conf import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def generate_thumbnail_image(topic: str):

    prompt = f"""
    Create a high-quality thumbnail image about:
    "{topic}" in the context of Korean education, robotics, AI, or creative learning.
    Style: modern, clean, bright colors, slightly futuristic but friendly.
    No text in the image.
    """

    res = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024"
    )

    b64 = res.data[0].b64_json
    img_bytes = base64.b64decode(b64)

    return ContentFile(img_bytes, name="thumbnail.png")
