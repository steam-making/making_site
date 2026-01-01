import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
import openpyxl  # 엑셀 저장용

def get_latest_round():
    url = "https://www.dhlottery.co.kr/common.do?method=main"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'lxml')
    latest = int(soup.select_one("strong#lottoDrwNo").text)
    return latest

def fetch_round(round_no):
    url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={round_no}"
    res = requests.get(url)
    data = res.json()
    return {
        "회차": data["drwNo"],
        "num1": data["drwtNo1"],
        "num2": data["drwtNo2"],
        "num3": data["drwtNo3"],
        "num4": data["drwtNo4"],
        "num5": data["drwtNo5"],
        "num6": data["drwtNo6"],
        "bonus": data["bnusNo"]
    }

def collect_recent(n_weeks=60):
    latest = get_latest_round()
    rows = []
    for r in range(latest, latest - n_weeks, -1):
        rows.append(fetch_round(r))
    df = pd.DataFrame(rows)
    return df

def save_to_excel(df, path="lotto_recent60.xlsx"):
    df.to_excel(path, index=False)
    print(f"저장 완료: {path}")

if __name__ == "__main__":
    df60 = collect_recent(60)
    save_to_excel(df60)
