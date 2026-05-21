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
apt_name = rf"data/서울시_행정동_아파트_월단위_202001_{previous_date}_base.csv"
global_name = rf"data/서울은행_글로발변수_월단위_202004_{previous_date}_base.csv"
people_name = rf"data/서울시_행정동_인구_월단위_202406_{previous_date}_base.csv"

data_name = rf"data/서울시_행정동_생활비용_월단위_202408_{previous_date}.csv"

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
merge_df = pd.merge(st_df,sales_df, on=["YYYYMM","행정동코드"], how="left")
merge_df = merge_df.drop(columns=["기준_년분기_코드"])

merge_df.to_csv(rf"data/서울시_행정동_시공간_합치기.csv", encoding="utf-8-sig", index=False)

# + 아파트
apt_df = apt_df[apt_df["YYYYMM"] >= pivot_date]

apt_df["행정동코드"] = apt_df["행정동코드"] * 100

merge_df = pd.merge(merge_df, apt_df, on=["YYYYMM","행정동코드"], how="outer")

# + 글로발

global_df.rename(columns={"TIME":"YYYYMM"}, inplace=True)

global_df = global_df[global_df["YYYYMM"] >= pivot_date]

merge_df = pd.merge(merge_df, global_df, on=["YYYYMM"], how="outer")

# + 인구
people_df = people_df[people_df["YYYYMM"] >= pivot_date]

people_df["행정동코드"] = people_df["행정동코드"] * 100

merge_df = pd.merge(merge_df, people_df, on=["YYYYMM","행정동코드"], how="outer")



merge_df.to_csv(rf"data/서울시_행정동_합치기.csv", encoding="utf-8-sig", index=False)








