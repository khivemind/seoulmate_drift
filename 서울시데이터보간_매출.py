import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.multioutput import MultiOutputRegressor
from datetime import datetime
from dateutil.relativedelta import relativedelta

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


# 2. 데이터 가져오기
sales_file = fr"data/서울시_상권분석_매출_행정동_총합_20194_{previous_season}_base.csv"

sales_df = pd.read_csv(sales_file, encoding="utf-8-sig")


print(f"{sales_file} 읽기")

# 행정동 공간 피처 합치기
space_df = pd.read_csv(r"data/서울시_행정동_공간_base.csv", encoding="utf-8-sig")

sales_df = pd.merge(sales_df,space_df,on="행정동코드", how="outer")

# sales_df.to_csv("서울시_행정동_매출_공간_임시.csv",
#                 encoding="utf-8-sig",
#                 index=False)

print(f"행정동 공간 갯수: {len(sales_df)}")
#sales_df.head(2)


# 3. 마지막 row 삽입
#last_season = sales_df["기준_년분기_코드"].max()
#season = next_quarter(last_season)

last_season = previous_season
season = now_season


last_df = sales_df[sales_df["기준_년분기_코드"] == last_season].copy()

# 마지막 분기 데이터 복사해서 다음 분기 삽입
new_df = last_df.copy()

new_df["당월_매출_금액"] = np.nan
new_df["당월_매출_건수"] = np.nan
new_df["기준_년분기_코드"] = season
print(f"add {season} data of {len(new_df)} rows")

# 한 번에 추가
sales_df = pd.concat([sales_df, new_df], ignore_index=True)

#sales_df.to_csv("서울시_행정동_매출_미래.csv", index=False, encoding="utf-8-sig")

# lag data
# feature engineering
# 모든 value column 이전 3부 lag data 기반으로 이번달 예측
# 이전 t-3개월 lag 데이터 기반으로 이번 t달 에측

value_cols = [
    "당월_매출_금액",
    "당월_매출_건수",
]

feat_cols = [

    "기준_년분기_코드",
    "행정동코드",

    "당월_매출_금액",
    "당월_매출_건수",

    # ── lag 피처: t-1, t-2, t-3 (이전달까지 확정값)
    "당월_매출_금액_lag1",
    "당월_매출_금액_lag2",
    "당월_매출_금액_lag3",

    "당월_매출_건수_lag1",
    "당월_매출_건수_lag2",
    "당월_매출_건수_lag3",

    # ── 통계 피처 (과거 기준)
    "당월_매출_금액_roll3_mean",
    "당월_매출_금액_roll3_std",
    "당월_매출_금액_change1",

    "당월_매출_건수_roll3_mean",
    "당월_매출_건수_roll3_std",
    "당월_매출_건수_change1",

    # ── 시간 피처
    "YEAR",
    "SEASON",
    "SEASON_SIN",
    "SEASON_COS",

    # 정적 피처
    "AREA_M2",
    "LAT",
    "LON",


]


# 정렬 다시 확인
sales_df = sales_df.sort_values(
    ["행정동코드", "기준_년분기_코드"]
)

group_df = sales_df.groupby("행정동코드")

sales_df["당월_매출_금액_lag1"] = group_df["당월_매출_금액"].shift(1)
sales_df["당월_매출_금액_lag2"] = group_df["당월_매출_금액"].shift(2)
sales_df["당월_매출_금액_lag3"] = group_df["당월_매출_금액"].shift(3)

sales_df["당월_매출_건수_lag1"] = group_df["당월_매출_건수"].shift(1)
sales_df["당월_매출_건수_lag2"] = group_df["당월_매출_건수"].shift(2)
sales_df["당월_매출_건수_lag3"] = group_df["당월_매출_건수"].shift(3)


sales_df["당월_매출_금액_roll3_mean"] = (group_df["당월_매출_금액"].transform(lambda x: x.shift(1).rolling(3).mean()))
sales_df["당월_매출_금액_roll3_std"] = (group_df["당월_매출_금액"].transform(lambda x: x.shift(1).rolling(3).std()))
sales_df["당월_매출_금액_change1"] = group_df["당월_매출_금액"].shift(1).pct_change(1)

sales_df["당월_매출_건수_roll3_mean"] = (group_df["당월_매출_건수"].transform(lambda x: x.shift(1).rolling(3).mean()))
sales_df["당월_매출_건수_roll3_std"] = (group_df["당월_매출_건수"].transform(lambda x: x.shift(1).rolling(3).std()))
sales_df["당월_매출_건수_change1"] = group_df["당월_매출_건수"].shift(1).pct_change(1)

sales_df['YEAR']     = sales_df['기준_년분기_코드'] // 10
sales_df['SEASON']    = sales_df['기준_년분기_코드'] %  10
sales_df['SEASON_SIN']= np.sin(2 * np.pi * sales_df['SEASON'] / 4)
sales_df['SEASON_COS']= np.cos(2 * np.pi * sales_df['SEASON'] / 4)


# "당월_매출_금액", "당월_매출_건수" 빼고 결측 있으면 삭제
check_cols = [col for col in sales_df.columns if col not in value_cols]
sales_df = sales_df.dropna(subset=check_cols)

# 정렬 다시 확인
sales_df = sales_df.sort_values(
    [ "기준_년분기_코드","행정동코드"]
)

feat_df = sales_df[feat_cols]

#feat_df.to_csv("서울시_행정동_매출_학습용.csv", index=False, encoding="utf-8-sig")

print('\n [결측치 확인]')
print(feat_df.isnull().sum())

print(len(feat_df))

feat_df.head(2)



# m2 학습용 데이터 분할
# 시계열로 분할

#feat_df = pd.read_csv("서울시_행정동_매출_학습용.csv",  encoding="utf-8-sig")

label_col = [
    "당월_매출_금액",
    "당월_매출_건수"
]

train_df = feat_df[(feat_df["기준_년분기_코드"] >= 20194) & (feat_df["기준_년분기_코드"] <= 20254)]
test_df = feat_df[(feat_df["기준_년분기_코드"] >= season) & (feat_df["기준_년분기_코드"] <= season)]


X_train = train_df.drop(columns=label_col)
y_train = train_df[label_col]

X_test = test_df.drop(columns=label_col)
y_test = test_df[label_col]

print("train:", X_train.shape)
print(f"train 기간: {X_train['기준_년분기_코드'].min()} - {X_train['기준_년분기_코드'].max()}")


print("train:", X_test.shape)
print(f"train 기간: {X_test['기준_년분기_코드'].min()} - {X_test['기준_년분기_코드'].max()}")


# LightGBM 모델
base_model = LGBMRegressor(
    n_estimators=1000,
    learning_rate=0.05
)

# Multi-output 래퍼
model = MultiOutputRegressor(base_model)

# 학습
model.fit(X_train, y_train)

# 예측
y_pred = model.predict(X_test)

# 결과 합치기
y_pred = y_pred.astype(int)

pred_df = pd.DataFrame(
    y_pred,
    columns=label_col
)

result_df = pd.concat(
    [X_test.reset_index(drop=True),
     pred_df.reset_index(drop=True)],
    axis=1
)

cols = [
    "기준_년분기_코드",
    "행정동코드",
    "당월_매출_금액",
    "당월_매출_건수"
    ]

result_df = result_df[cols]

# 이전것과 합치기

sales_df = pd.read_csv(sales_file,encoding="utf-8-sig")
sales_df = sales_df.astype(int)

concat_df = pd.concat(
    [sales_df[cols], result_df[cols]],
    ignore_index=True
)

concat_df.to_csv(rf"data/서울시_상권분석_매출_행정동_총합_20194_{now_season}_base.csv", index=False, encoding="utf-8-sig")

print(rf"data/서울시_상권분석_매출_행정동_총합_20194_{now_season}_base.csv 생성")


#
# 월단위로 쪼개기
#

sales_df = concat_df

# interpolate를 통해서 월단위 데이터 전환

# 분기 -> 월 매핑
quarter_month_map = {
    "1": "03",
    "2": "06",
    "3": "09",
    "4": "12"
}

value_cols = [
    "당월_매출_금액",
    "당월_매출_건수",
]

code_cols = [
    "기준_년분기_코드",
    "행정동코드"
]


# YYYYQ -> YYYYMM 변환
sales_df["YYYYMM"] = (
    sales_df["기준_년분기_코드"]
    .astype(str)
    .str[:4]
    +
    sales_df["기준_년분기_코드"]
    .astype(str)
    .str[-1]
    .map(quarter_month_map)
)

result = []

# 행정동별 월 보간
for code, g in sales_df.groupby("행정동코드"):

    g = g.copy()

    # 날짜 변환
    g["DATE"] = pd.to_datetime(
        g["YYYYMM"],
        format="%Y%m"
    )

    g = g.sort_values("DATE")

    # index 설정
    g = g.set_index("DATE")


    # 월 단위 확장
    monthly = g.resample("MS").asfreq()

    # 수치 컬럼 보간
    monthly[value_cols] = (
        monthly[value_cols]
        .interpolate(method="linear")
    )

    # code 채우기
    monthly[code_cols] = (
        monthly[code_cols]
        .ffill()
    )

    # 행정동코드 유지
    monthly["행정동코드"] = code

    # YYYYMM 생성
    monthly["YYYYMM"] = (
        monthly.index.strftime("%Y%m")
    )

    result.append(monthly)


# 합치기
monthly_sales_df = (
    pd.concat(result)
    .reset_index(drop=True)
)


monthly_sales_df[value_cols] = (
    monthly_sales_df[value_cols]
    .round()
    .fillna(0)
    .astype(int)

)

monthly_sales_df[code_cols] = (
    monthly_sales_df[code_cols]
    .ffill()
)

monthly_sales_df = (
    monthly_sales_df
    .sort_values(
        ["YYYYMM", "행정동코드"]
    )
    .reset_index(drop=True)
)


previous_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달
now_date = datetime.today().strftime("%Y%m")


monthly_sales_df[[
    "기준_년분기_코드",
    "YYYYMM",
    "행정동코드",
    "당월_매출_금액",
    "당월_매출_건수"]].to_csv(
    rf"data/서울시_행정동_매출_월단위_201910_{previous_date}.csv",
    index=False,
    encoding="utf-8-sig")


print(f"갯수: {len(monthly_sales_df)}")
monthly_sales_df.head(2)



















