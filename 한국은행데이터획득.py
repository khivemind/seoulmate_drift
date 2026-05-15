import pandas as pd
import requests
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
from functools import reduce

API_KEY = "MPA5HD9SWCXKHC7G7QTS"

SERVICES ={
    "161Y005": "BBHS00",           # M2              2달 지연
    "901Y014": "1080000",          # KOSPI_평균       2달 지연
    "901Y062": "P63AD",            # 주택매매가격지수(KB),총지수(서울)   1달 지연
    "901Y063": "P64AD",            # 주택전세가격지수(KB),총지수(서울)   1달 지연
    "731Y004": "0000001",          # 환율, 원/미국달러(매매기준율)       1달 지연
#    "405Y006": "*A"                # 국내공급물가지수 데이터부족으로 제외
}


start_date = "202601"
#end_date = "202604"
end_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달

file_name = f"서울은행_글로발변수_월단위_{start_date}_{end_date}.csv"

#
# M2
#
def get_m2():
    SERVICE = "161Y005"
    ITEM = SERVICES[SERVICE]

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/1000/{SERVICE}/M/{start_date}/{end_date}"

    print(url)

    response = requests.get(url)

    data = response.json()

    body = data["StatisticSearch"]

    rows = body["row"]

    df = pd.DataFrame(rows)

    # ITEM_CODE1 == BBHS00 필터
    total_df = df[df["ITEM_CODE1"] == ITEM]

    m2_df = total_df.rename(columns={"DATA_VALUE":"M2"})[["TIME","M2"]]

    print(f"m2 data size:{len(m2_df)}")
    m2_df.head(2)

    return m2_df

#
# kospi
#
def get_kospi():
    SERVICE = "901Y014"
    ITEM = SERVICES[SERVICE]

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/1000/{SERVICE}/M/{start_date}/{end_date}"

    print(url)

    response = requests.get(url)

    data = response.json()

    body = data["StatisticSearch"]

    rows = body["row"]

    df = pd.DataFrame(rows)

    total_df = df[df["ITEM_CODE1"] == ITEM]

    kopsi_df = total_df.rename(columns={"DATA_VALUE":"KOSPI"})[["TIME","KOSPI"]]

    print(f"kopsi data size:{len(kopsi_df)}")
    kopsi_df.head(2)

    return kopsi_df
#
# house sale index
#
def get_house():
    SERVICE = "901Y062"
    ITEM = SERVICES[SERVICE]

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/1000/{SERVICE}/M/{start_date}/{end_date}"

    print(url)

    response = requests.get(url)

    data = response.json()

    body = data["StatisticSearch"]

    rows = body["row"]

    df = pd.DataFrame(rows)

    total_df = df[df["ITEM_CODE1"] == ITEM]

    house_sale_df = total_df.rename(columns={"DATA_VALUE": "HOUSE_SALE"})[["TIME", "HOUSE_SALE"]]

    print(f"house sale data size:{len(house_sale_df)}")
    house_sale_df.head(2)

    return house_sale_df
#
# rent sale index
#
def get_rent():
    SERVICE = "901Y063"
    ITEM = SERVICES[SERVICE]

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/1000/{SERVICE}/M/{start_date}/{end_date}"

    print(url)

    response = requests.get(url)

    data = response.json()

    body = data["StatisticSearch"]

    rows = body["row"]

    df = pd.DataFrame(rows)

    total_df = df[df["ITEM_CODE1"] == ITEM]

    rent_sale_df = total_df.rename(columns={"DATA_VALUE": "RENT_SALE"})[["TIME", "RENT_SALE"]]

    print(f"rent sale data size:{len(rent_sale_df)}")
    rent_sale_df.head(2)

    return rent_sale_df
#
# fx sale index
#
def get_fx():
    SERVICE = "731Y004"
    ITEM = SERVICES[SERVICE]

    url = f"https://ecos.bok.or.kr/api/StatisticSearch/{API_KEY}/json/kr/1/3000/{SERVICE}/M/{start_date}/{end_date}"

    print(url)

    response = requests.get(url)

    data = response.json()

    body = data["StatisticSearch"]

    rows = body["row"]

    df = pd.DataFrame(rows)

    total_df = df[(df["ITEM_CODE1"] == ITEM) & (df["ITEM_CODE2"] == "0000100")]

    fx_df = total_df.rename(columns={"DATA_VALUE": "FX"})[["TIME", "FX"]]

    print(f"fx data size:{len(fx_df)}")
    fx_df.head(2)

    return fx_df


#
# merge data
#
dfs = [get_m2(), get_kospi(), get_house(), get_rent(), get_fx()]
global_df = reduce(
    lambda l, r:
        pd.merge(l,r,on="TIME", how="outer"),
    dfs
)

# 저장
global_df.to_csv(
     file_name,
     index=False,
     encoding="utf-8-sig"
)

# 결측 데이터 확인
with open(file_name, 'rb') as f:
    result = chardet.detect(f.read(10000))

print(file_name, result)

df = pd.read_csv(file_name)

print(df.isnull().sum())








