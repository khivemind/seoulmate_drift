import pandas as pd
import requests
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

API_KEY = "776866746a73796236356c51455047"

#start_date = "202601"
#end_date = "202604"
start_date = (datetime.today() - relativedelta(months=2)).strftime("%Y%m")      # 오늘 기준 이전전달
end_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달


# SERVICES = {
#     "VwsmAdstrdSelngW":f"서울시_상권분석_매출_행정동_{start_date}_{end_date}.csv",
#     "VwsmAdstrdAptW":f"서울시_아파트_평균가격_행정동_{start_date}_{end_date}.csv",
#     "tpssPassengerCnt":f"서울시_행정동_대중교통_승차수_{start_date}_{end_date}.csv",
#     "SPOP_LOCAL_RESD_DONG":f"서울시_행정동_생활인구_{start_date}_{end_date}.csv"
# }

SERVICE = "tpssPassengerCnt"        # 행정동단위
file_name = f"data/서울시_행정동_대중교통_승차수_{start_date}_{end_date}.csv"
tmp_file = f"data/서울시_행정동_대중교통_승차수_{start_date}_{end_date}_tmp.csv"

edm_name = f"data/서울시_행정동ID_행정동코드_맵핑_base.csv"

#BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json/{SERVICE}"
BASE_URL = f"http://openapi.seoul.go.kr:8088/{API_KEY}/json"

def get_total_count(service):
    # 전체 갯수 확인

    url = f"{BASE_URL}/{service}/1/1/"

    print(f"요청 {url}")

    # 요청
    response = requests.get(url)

    # 응답 JSON 변환
    data = response.json()

    body = data.get(service, {})

    # 상태 체크
    result_code = body.get("RESULT", {}).get("CODE")
    if result_code != "INFO-000":
        raise Exception(f"API 오류: {body.get('RESULT')}")

    total_count = body.get("list_total_count", 0)

    print("총 데이터 수:", total_count)

    return total_count

def get_traffic():
#    SERVICE = "tpssPassengerCnt"
#    tmp_file = SERVICES[SERVICE]

    total_count = get_total_count(SERVICE)
    
    # 전체를 1000개 단위로 읽어오고 csv로 저장
    # 날자 내림 차순으로 보이지만 확신할수 없다. 전체 받고 날자로 필터링 하기

    is_first = True
    
    step = 1000
    ranges = [(i, min(i + step - 1, total_count)) for i in range(1, total_count + 1, step)]

    if os.path.exists(tmp_file):
        os.remove(tmp_file)

    for s, e in ranges:
        url = f"{BASE_URL}/{SERVICE}/{s}/{e}/"

        print(f"요청 {url}")

        response = requests.get(url)
    
        data = response.json()
    
        body = data[SERVICE]
    
        result_code = body["RESULT"]["CODE"]
        if result_code != "INFO-000":
            raise Exception(f"API 오류: {body.get('RESULT')}")
    
        rows = body["row"]
    
        if not rows:
            continue


        # 최신날짜부터 item을 가저온다
        # 첫 item 날자가 start_date보다 크면 중지

        first_item = rows[0]

        if first_item["CRTR_DD"][:6] < start_date:
            print(f"item 시간: {first_item['CRTR_DD'][:6]}  > 시작 시간 : {start_date} 임으로 건너뛰기 ")
            break

        df = pd.DataFrame(rows)
    
        df.to_csv(
            tmp_file,
            mode="a",
            index=False,
            header=is_first,
            encoding="utf-8-sig"
        )
    
        is_first = False
    
        del df


    # 기간 필터링
    df = pd.read_csv(tmp_file, encoding="utf-8-sig")

    filter_df = df.rename(columns={
        "CRTR_DD":"기준_날짜",
        "DONG_ID":"행정동_ID",
        "PSNG_NO":"승객_수"
    })

    filter_df["YYYYMM"] = (
        filter_df["기준_날짜"]
        .astype(str)
        .str[:6]
    )

    filter_df = filter_df[(filter_df["YYYYMM"] >= start_date) & (filter_df["YYYYMM"] <= end_date)]

    filter_df["승객_수"] = pd.to_numeric(
        filter_df["승객_수"],
        errors="coerce"
    ).fillna(0).astype(int)

    filter_df["승객_수"] = filter_df["승객_수"].astype(int)

    result_df = (
        filter_df
        .groupby(["YYYYMM", "행정동_ID"])["승객_수"]
        .sum()
        .reset_index()
        .sort_values(["YYYYMM", "행정동_ID"])
    )

    # 행정동코드
    #emd_df = pd.read_csv(edm_name, encoding="utf-8-sig")

    #result_df = pd.merge(result_df, emd_df, on="행정동_ID", how="outer")

    result_df.to_csv(file_name, index=False, encoding="utf-8-sig" )


# data 가저오기

get_traffic()
