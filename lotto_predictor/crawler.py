import requests
import pandas as pd
from pathlib import Path
from django.utils import timezone
from .models import LottoResult

def update_lotto_results():
    """
    동행복권 API를 사용해 최신 회차까지 DB 업데이트.
    - DB를 최신화하고
    - 모든 회차를 lotto_results.xlsx 로 저장
    """
    url = "https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={}"

    # 현재 DB 최신 회차
    try:
        latest = LottoResult.objects.latest("draw_no").draw_no
    except LottoResult.DoesNotExist:
        latest = 0

    next_no = latest + 1
    new_count = 0

    while True:
        resp = requests.get(url.format(next_no))
        data = resp.json()
        if data.get("returnValue") != "success":
            break  # 더 이상 새로운 회차 없음 → 종료

        numbers = [data[f"drwtNo{i}"] for i in range(1, 7)]
        LottoResult.objects.update_or_create(
            draw_no=next_no,
            defaults={
                "numbers": ",".join(map(str, numbers)),
                "bonus": data["bnusNo"],
            },
        )
        next_no += 1
        new_count += 1

    # ✅ 전체 DB를 DataFrame으로 불러오기
    all_data = LottoResult.objects.all().order_by("draw_no").values(
        "draw_no", "numbers", "bonus"
    )
    df = pd.DataFrame(all_data)

    # ✅ 숫자 분리해서 num1~num6 컬럼 추가
    if not df.empty:
        nums = df["numbers"].str.split(",", expand=True)
        nums.columns = [f"num{i}" for i in range(1, 7)]
        df = pd.concat([df.drop(columns=["numbers"]), nums], axis=1)
        df = df[["draw_no", "num1", "num2", "num3", "num4", "num5", "num6", "bonus"]]

    # ✅ 파일 경로 지정 (프로젝트 루트 기준)
    output_dir = Path(__file__).resolve().parent
    excel_path = output_dir / "lotto_results.xlsx"

    # ✅ 엑셀로 저장 (인덱스 없이)
    df.to_excel(excel_path, index=False)

    print(f"📁 로또 데이터 {len(df)}회차 엑셀 저장 완료: {excel_path}")
    if new_count:
        print(f"✅ 새로 추가된 회차: {new_count}개")
    else:
        print("🔄 이미 최신 상태입니다.")

    return len(df)
