# blog_auto/services/naver_api_selenium.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def slow_type_actionchains(element, text, driver, delay=0.01):
    """ActionChains로 1글자씩 입력"""
    actions = ActionChains(driver)
    element.click()
    time.sleep(0.2)

    for ch in text:
        actions.send_keys(ch)
        actions.perform()
        time.sleep(delay)


def publish_to_naver_selenium(post, blog_id="steam_making"):

    WRITE_URL = f"https://blog.naver.com/{blog_id}/postwrite"

    options = Options()
    options.add_argument(r"user-data-dir=E:\selenium_chrome_profile")
    options.add_argument("profile-directory=Default")
    options.add_experimental_option("detach", True)   # 자동 종료 방지

    # 자동화 탐지 최소화
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    print("🚀 네이버 글쓰기 접속...")
    driver.get(WRITE_URL)
    time.sleep(3)

    # ────────────────────────────────────
    # 1) 제목 placeholder 클릭 → 스페이스 → 입력
    # ────────────────────────────────────
    print("⏳ 제목 placeholder 대기...")
    title_placeholder = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-title-text .se-placeholder"))
    )

    print("👉 제목 placeholder 클릭")
    title_placeholder.click()
    time.sleep(0.2)

    # placeholder 제거를 위해 스페이스 입력
    actions = ActionChains(driver)
    actions.send_keys(" ")
    actions.perform()
    time.sleep(0.2)

    print("⏳ 실제 입력 노드(span.__se-node) 대기...")
    title_node = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            ".se-title-text span.__se-node"
        ))
    )

    print("✏️ 제목 입력 중...")
    slow_type_actionchains(title_node, post.main_title, driver)

    time.sleep(0.5)

    # ────────────────────────────────────
    # 2) 본문 placeholder 클릭 → 스페이스 → 입력
    # ────────────────────────────────────
    print("⏳ 본문 placeholder 대기...")
    body_placeholder = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".se-component.se-text .se-placeholder")
        )
    )

    print("👉 본문 placeholder 클릭")
    body_placeholder.click()
    time.sleep(0.2)

    actions.send_keys(" ")  # placeholder 제거용 스페이스
    actions.perform()
    time.sleep(0.2)

    print("⏳ 본문 입력 노드(span.__se-node) 대기...")
    body_node = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            ".se-component.se-text span.__se-node"
        ))
    )

    print("✏️ 본문 입력 중...")
    slow_type_actionchains(body_node, post.content, driver)

    time.sleep(0.8)

    # ────────────────────────────────────
    # 3) 발행 버튼 클릭
    # ────────────────────────────────────
    print("📤 1차 발행 버튼 클릭 대기...")
    publish_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.publish_btn__m9KHH"))
    )

    print("📤 1차 발행 버튼 클릭!")
    publish_btn.click()
    
    print("📤 2차 발행 버튼 클릭 대기...")

    publish_btn = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[data-testid="seOnePublishBtn"]')
        )
    )

    print("📤 2차 발행 버튼 클릭!")
    publish_btn.click()

    print("🎉 발행 완료!")

    return driver.current_url
