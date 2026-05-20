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
filled_file_name = f"data/서울시_행정동_아파트_월단위_월단위_{start_date}_{end_date}_base.csv"

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


