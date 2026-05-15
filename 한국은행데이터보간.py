import pandas as pd
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fontTools.misc.cython import returns
from sklearn.linear_model import RidgeCV, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

start_date = "202004"
#end_date = "202512"
end_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달

file_name = f"서울은행_글로발변수_월단위_{start_date}_{end_date}.csv"
filled_file_name = f"서울은행_글로발변수_월단위_{start_date}_{end_date}_filled.csv"

# 2. 데이터 가져오기
global_df = pd.read_csv(file_name, encoding="utf-8-sig")
print(f"{file_name}의 item 갯수 {len(global_df)}")

print(f"마지막줄을 제외한 데이터에 결측이 있는가 : {global_df.iloc[:-1].isna().any().any()}")
print(f"마지막줄의 m2,kospi 빼고 결측 있는가 : {global_df.iloc[-1].drop(['M2','KOSPI']).isna().any()}")

assert global_df.iloc[:-1].isna().any().any() == False, \
    f"{file_name}에 마지막줄 제외한 데이터에도 결측이 있습니다. 확인해주십시요"

assert global_df.iloc[-1].drop(['M2','KOSPI']).isna().any() == False, \
    f"{file_name}에 마지막줄에 M2,KOSPI를 제외한 값에 결측이 있습니다. 확인해주십시요"


# lag data
# feature engineering
# 모든 value column 이전 3개월 lag data 기반으로 이번달 예측
# 이전 t-3개월 lag 데이터 기반으로 이번 t달 에측

data_cols = [
    'TIME',
    'M2',
    'KOSPI',
    'HOUSE_SALE',
    'RENT_SALE',
    'FX'
]


value_cols = [
    'M2',
    'KOSPI',
    'HOUSE_SALE',
    'RENT_SALE',
    'FX'
]

feat_cols = [

    'TIME',
    'M2',
    'KOSPI',
    'HOUSE_SALE',
    'RENT_SALE',
    'FX'

    "M2_lag1",
    "KOSPI_lag1",
    "HOUSE_SALE_lag1",
    "RENT_SALE_lag1",
    "FX_lag1"
]

for col in value_cols:
    lag1 = f"{col}_lag1"

    global_df[lag1] = global_df[col].shift(1)

# 학습용 데이터, 처음 마지막 제외

last_df = global_df.tail(1).copy()

train_df = global_df.iloc[1:].iloc[:-1].copy()

cost_index = "M2"
kospi_index = "KOSPI"

X_train = train_df.drop(columns=cost_index)
y_train = train_df[cost_index]

X_kospi_train = train_df.drop(columns=kospi_index)
y_kospi_train = train_df[kospi_index]

print("train:", X_train.shape)
print(f"train 기간: {X_train['TIME'].min()} - {X_train['TIME'].max()}")

print("train:", X_kospi_train.shape)
print(f"train 기간: {X_kospi_train['TIME'].min()} - {X_kospi_train['TIME'].max()}")

# ml으로 m2, kospi 결측 예측
m2_model = Pipeline([
    ("scale",StandardScaler()),
    ("model",ElasticNet(
        alpha=0.1,
        l1_ratio=0.5
    ))
])

m2_model.fit(X_train, y_train)

kospi_model = Pipeline([
    ("scale",StandardScaler()),
    ("model",ElasticNet(
        alpha=0.1,
        l1_ratio=0.5
    ))
])

kospi_model.fit(X_kospi_train, y_kospi_train)

# 결측 예측
kospi_x = last_df.drop("KOSPI", axis=1)

kospi_x["M2"] = kospi_x["M2_lag1"]  # 임시로 lag1 사용
kospi_pred = kospi_model.predict(kospi_x)

m2_x = last_df.drop("M2", axis=1)
m2_x["KOSPI"] = kospi_pred[0]
m2_pred = m2_model.predict(m2_x)

last_df["KOSPI"] = kospi_pred
last_df["M2"] = m2_pred

print(f"결측 보간 완료 : ")
print(last_df)

# 저장

filled_df = pd.concat([train_df,last_df], ignore_index=True).sort_values("TIME").reset_index(drop=True)[data_cols]

filled_df.to_csv(filled_file_name,index=False, encoding="utf-8-sig")







