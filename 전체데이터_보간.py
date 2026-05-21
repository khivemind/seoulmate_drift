import pandas as pd
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os


# 다음 분기 코드
def next_quarter(code):
    year = code // 10      # 20261 -> 2026
    quarter = code % 10    # 20261 -> 1

    if quarter == 4:
        year += 1
        quarter = 1
    else:
        quarter += 1

    return year * 10 + quarter

# 이전 분기 코드
def previous_quarter(code):
    year = code // 10      # 20261 -> 2026
    quarter = code % 10    # 20261 -> 1

    if quarter == 1:
        year -= 1
        quarter = 4
    else:
        quarter -= 1

    return year * 10 + quarter


# 데이터 보간 하기
# 예외처리
# 비었다면, 행정동코드가 같은 가장 가까운 YYYYMM으로 값을 채움

def interpolate_columns(cols, data_df) -> pd.DataFrame:

    pandas_df = data_df.copy()

    # YYYYMM 기준 정렬
    pandas_df = pandas_df.sort_values(
        ["행정동코드", "YYYYMM"]
    )

    # 행정동별 보간
    for col in cols:
        pandas_df[col] = (
            pandas_df
            .groupby("행정동코드")[col]
            .transform(
                lambda x: x.interpolate(
                    method="linear",
                    limit_direction="both"
                )
            )
        )

    return pandas_df

# 지금 분기
now = datetime.now()
year = now.year
quarter = (now.month - 1) // 3 + 1

now_season = int(f"{year}{quarter}")
previous_season = previous_quarter(now_season)

# 지금 시간
previous_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달
now_date = datetime.today().strftime("%Y%m")      # 이번달

#
#   수집된 데이터
#

spatiotemporal_name = rf"data/서울시_행정동_시공간_월단위_202408_{previous_date}_base.csv"
sales_name = rf"data/서울시_행정동_매출_월단위_201910_{previous_date}_base.csv"
apt_name = rf"data/서울시_행정동_아파트_월단위_202406_{previous_date}_base.csv"
global_name = rf"data/서울은행_글로발변수_월단위_202004_{previous_date}_base.csv"
people_name = rf"data/서울시_행정동_인구_월단위_202406_{previous_date}_base.csv"

data_name = rf"data/생활비용_모델용_월단위_202408_{previous_date}.csv"

#   202408 부터 현재까지 이전달까지 학습용 데이터 생성
global_df = pd.read_csv(global_name, encoding="utf-8-sig")
st_df = pd.read_csv(spatiotemporal_name, encoding="utf-8-sig")
people_df = pd.read_csv(people_name, encoding="utf-8-sig")
sales_df = pd.read_csv(sales_name, encoding="utf-8-sig")
apt_df = pd.read_csv(apt_name, encoding="utf-8-sig")

pivot_date = 202408

# 시공간 + 매출
st_df = st_df[st_df["YYYYMM"] >= pivot_date]
sales_df = sales_df[sales_df["YYYYMM"] >= pivot_date]

st_df = st_df.drop_duplicates(subset=["YYYYMM", "행정동코드"])
sales_df = sales_df.drop_duplicates(subset=["YYYYMM", "행정동코드"])

merge_df = pd.merge(st_df,sales_df, on=["YYYYMM","행정동코드"], how="left")
merge_df = merge_df.drop(columns=["기준_년분기_코드"])

merge_df = interpolate_columns(["당월_매출_금액", "당월_매출_건수"], merge_df)

merge_df.to_csv(rf"data/서울시_행정동_시공간_합치기.csv", encoding="utf-8-sig", index=False)


# + 아파트
apt_df = apt_df[apt_df["YYYYMM"] >= pivot_date]
apt_df = apt_df.drop_duplicates(subset=["YYYYMM", "행정동코드"])

merge_df = pd.merge(merge_df, apt_df, on=["YYYYMM","행정동코드"], how="left")

# 쓸모없는 컬럼 삭제
merge_df.drop(columns=["기준_년분기_코드","행정동_코드_명"],inplace=True)

# 개포3동, 상일1동, 상일2동, 둔촌1동 데이터가 없다
# 예외처리 상일동 1174052000 -> 상일제1동 1174052500, 상일제2동 1174052600 분리
# 예외처리 일원2동 1168074000 -> 개포3동 1168067500
# 예외처리 둔촌1동 1174069000 -> 둔촌2동 1174070000의 복사


merge_df = interpolate_columns(["아파트_단지_수",""
                                "아파트_면적_66_제곱미터_미만_세대_수",
                                "아파트_면적_66_제곱미터_세대_수",
                                "아파트_면적_99_제곱미터_세대_수",
                                "아파트_면적_132_제곱미터_세대_수",
                                "아파트_면적_165_제곱미터_세대_수",
                                "아파트_평균_면적","아파트_평균_시가"], merge_df)

merge_df.to_csv(rf"data/서울시_행정동_아파트_합치기.csv", encoding="utf-8-sig", index=False)



# + 글로발

global_df.rename(columns={"TIME":"YYYYMM"}, inplace=True)

global_df = global_df[global_df["YYYYMM"] >= pivot_date]

merge_df = pd.merge(merge_df, global_df, on=["YYYYMM"], how="outer")

# + 인구
people_df = people_df[people_df["YYYYMM"] >= pivot_date]

people_df = people_df.drop_duplicates(subset=["YYYYMM", "행정동코드"])

people_df["행정동코드"] = people_df["행정동코드"] * 100

merge_df = pd.merge(merge_df, people_df, on=["YYYYMM","행정동코드"], how="outer")

merge_df.dropna(inplace=True)
print(merge_df.isnull().sum())

merge_df.to_csv(data_name, encoding="utf-8-sig", index=False)








