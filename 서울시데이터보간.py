import pandas as pd
# import chardet
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# from fontTools.misc.cython import returns
# from sklearn.linear_model import RidgeCV, ElasticNet
# from sklearn.preprocessing import StandardScaler
# from sklearn.pipeline import Pipeline
# import numpy as np

from datetime import datetime
from dateutil.relativedelta import relativedelta


start_date = 202001
middle_date = (datetime.today() - relativedelta(months=2)).strftime("%Y%m")      # 오늘 기준 이전전달
end_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달

base_file_name = f"data/서울시_행정동_아파트_월단위_{start_date}_{middle_date}_base.csv"
filled_file_name = f"data/서울시_행정동_아파트_월단위_{start_date}_{end_date}_base.csv"
##############
# 아파트
# 2. 데이터 가져오기
base_df = pd.read_csv(base_file_name, encoding="utf-8-sig")

last_df = base_df[base_df["YYYYMM"] == int(middle_date)].copy()

# 3. 저저번달 데이터 복사해서 저번달에 삽입
new_df = last_df.copy()

print(f"add {int(end_date)} data of {len(new_df)} rows")

new_df["YYYYMM"] = int(end_date)


# 한 번에 추가
base_df = pd.concat([base_df, new_df], ignore_index=True)

base_df.to_csv(filled_file_name, index=False, encoding="utf-8-sig")


############################
# 시공간
space_df = pd.read_csv(r"data/서울시_행정동_공간_base.csv", encoding="utf-8-sig")
traffic_df = pd.read_csv(rf"data/서울시_행정동_대중교통_승차수_{middle_date}_{end_date}.csv", encoding="utf-8-sig")
emd_df = pd.read_csv(r"data/서울시_행정동ID_행정동코드_맵핑_base.csv", encoding="utf-8-sig")

traffic_df.rename(columns={"승객_수":"전체승객수"}, inplace=True)
traffic_df = pd.merge(traffic_df,emd_df, on="행정동_ID", how="outer")


cols = [
    "YYYYMM",
    "행정동코드",
    "행정동이름",
    "AREA_M2",
    "LAT",
    "LON",
    "전체승객수"
    ]


merge_df = pd.merge(traffic_df, space_df, on="행정동코드", how="outer")
merge_df = merge_df[cols].copy()

merge_df.to_csv(rf"data/서울시_행정동_시공간_월단위_{middle_date}_{end_date}", index=False, encoding="utf-8-sig")
st_df = pd.read_csv(rf"data/서울시_행정동_시공간_월단위_202408_{middle_date}_base.csv", encoding="utf-8-sig")

st_df = st_df[cols].copy()

base_df = pd.concat([st_df, merge_df], ignore_index=True)

base_df = base_df.dropna()

base_df = base_df.sort_values(
    by=["YYYYMM", "행정동코드"]
)

base_df = base_df.astype({
    "YYYYMM": int,
    "행정동코드": int,
    "AREA_M2": int,
    "전체승객수": int
})


base_df.to_csv(rf"data/서울시_행정동_시공간_월단위_202408_{end_date}_base.csv",
               index=False,
               encoding="utf-8-sig")



