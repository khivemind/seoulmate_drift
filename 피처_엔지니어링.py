import pandas as pd
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import numpy as np

# 지금 시간
previous_date = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")      # 오늘 기준 이전달
now_date = datetime.today().strftime("%Y%m")      # 이번달

#
#   전처리된 데이터
#

data_name = rf"data/생활비용_모델용_월단위_202408_{previous_date}.csv"
data_df = pd.read_csv(data_name, encoding="utf-8-sig")

print(f"{data_name}의 item 갯수 {len(data_df)}")
print(data_df.head(2))

#3. 데이터 전처리
print('\n [결측치 확인]')
print(data_df.isnull().sum())

# 2차
# 생활비용지수 (CLI) =  w1*소비강도 + w2*주거비용 + w3*수요압력 + w4*거시환경
# 소비강도 = Z((당월매출금액/생활인구합계)
# 주거비용 = Z(아파트평균시가/평균가족구성원수/아파트_평균_면적)+0.2*서울전세가격지수+0.2*서울주택매매지수
# 수요압력 = Z(전체승객수/행정동면적)
# 거시환경 = Z(M2)+Z(FX)-Z(KOSPI)
# Z는 z-score 또는 log1p 으로 튜닝
# w1=0.5, w2=0.3,w3=0.15,w4=0.05를 시작으로 튜닝
# CLI=0.5*Z((당월매출금액/생활인구합계)+0.3*(Z(아파트평균시가/평균가족구성원수/아파트_평균_면적)+0.2*서울전세가격지수+0.2*서울주택매매지수)+0.15*Z(전체승객수/행정동면적)+0.05*(Z(M2)+Z(FX)-Z(KOSPI))

data_df["생활비용지수"] = 0.5*np.log1p(data_df["당월_매출_금액"]/data_df["생활인구합계"])     \
                        + 0.3*np.log1p(data_df["아파트_평균_시가"]/2/data_df["아파트_평균_면적"]+0.2*data_df["HOUSE_SALE"]+0.2*data_df["RENT_SALE"])        \
                        + 0.15*np.log1p(data_df["전체승객수"]/data_df["AREA_M2"])        \
                        + 0.05*(np.log1p(data_df["M2"])+np.log1p(data_df["FX"])-np.log1p(data_df["KOSPI"]))


# feature engineering
# 행정동에 대하여 이전 3개월 lag data 기반으로 이번달 예측
# 이전 t-3개월 lag 데이터 기반으로 이번 t달 에측

cols = [
    "YYYYMM",
    "행정동코드"
    "행정동이름"
    "당월_매출_금액",
    "당월_매출_건수",
    "주중_매출_금액",
    "주말_매출_금액",
    "남성_매출_금액",
    "여성_매출_금액",
    "AREA_M2",
    "LAT",
    "LON",
    "전체승객수",
    "지하철승객수",
    "버스승객수",
    "아파트_단지_수",
    "아파트_면적_66_제곱미터_미만_세대_수",
    "아파트_면적_66_제곱미터_세대_수",
    "아파트_면적_99_제곱미터_세대_수",
    "아파트_면적_132_제곱미터_세대_수",
    "아파트_면적_165_제곱미터_세대_수",
    "아파트_평균_면적",
    "아파트_평균_시가",
    "M2",
    "KOSPI",
    "HOUSE_SALE",
    "RENT_SALE",
    "FX",
    "생활인구합계",
    "생활비용지수"
]

feat_cols = [

    'YYYYMM',

    '행정동코드',   # LightGBM categorical

    '생활비용지수',

    # ── lag 피처: t-1, t-2, t-3 (이전달까지 확정값)
    "생활비용지수_lag1",
    "생활비용지수_lag2",
    "생활비용지수_lag3",

    # ── 통계 피처 (과거 기준)
    "생활비용지수_roll3_mean",
    "생활비용지수_roll3_std",
    "생활비용지수_change1",
    "생활비용지수_change3_mean",

    # ── 시간 피처
    "YEAR",
    "MONTH",
    "MONTH_SIN",
    "MONTH_COS",

    # ── 거시 피처
    "KOSPI_lag1",
    "M2_lag1",
    "FX_lag1",
    "HOUSE_SALE_lag1",
    "RENT_SALE_lag1",

    # ── 매출·인구
    "당월_매출_금액_lag1",
    "생활인구합계_lag1",
    "전체승객수_lag1",

    # ── 부동산가격
    "아파트_평균_시가_lag1",

    # 정적 피처
    "AREA_M2",
    "LAT",
    "LON",
    "아파트_단지_수",
    "아파트_면적_66_제곱미터_미만_세대_수",
    "아파트_면적_66_제곱미터_세대_수",
    "아파트_면적_99_제곱미터_세대_수",
    "아파트_면적_132_제곱미터_세대_수",
    "아파트_면적_165_제곱미터_세대_수",
    "아파트_평균_면적",
]


#
# 예측용 이번달 row 넣기, feat row는 생성됨
#

last_yyyymm = data_df["YYYYMM"].max()

last_rows = data_df[
    data_df["YYYYMM"] == last_yyyymm
].copy()

last_rows['YYYYMM'] = pd.to_numeric(now_date)

data_df = pd.concat(
    [data_df, last_rows],
    ignore_index=True)






#
# 정렬 다시 확인
#
data_df = data_df.sort_values(
    ["행정동코드", "YYYYMM"]
)

group_df = data_df.groupby("행정동코드")

data_df["생활비용지수_lag1"] = group_df["생활비용지수"].shift(1)
data_df["생활비용지수_lag2"] = group_df["생활비용지수"].shift(2)
data_df["생활비용지수_lag3"] = group_df["생활비용지수"].shift(3)

data_df["생활비용지수_roll3_mean"] = (group_df["생활비용지수"].transform(lambda x: x.shift(1).rolling(3).mean()))
data_df["생활비용지수_roll3_std"] = (group_df["생활비용지수"].transform(lambda x: x.shift(1).rolling(3).std()))

data_df["생활비용지수_change1"] = group_df["생활비용지수"].shift(1).pct_change(1)
data_df["생활비용지수_change3_mean"] = group_df["생활비용지수_change1"].transform(lambda x: x.shift(1).rolling(3).mean())

data_df["KOSPI_lag1"] = group_df["KOSPI"].shift(1)
data_df["M2_lag1"] = group_df["M2"].shift(1)
data_df["FX_lag1"] = group_df["FX"].shift(1)
data_df["HOUSE_SALE_lag1"] = group_df["HOUSE_SALE"].shift(1)
data_df["RENT_SALE_lag1"] = group_df["RENT_SALE"].shift(1)

data_df["당월_매출_금액_lag1"] = group_df["당월_매출_금액"].shift(1)
data_df["생활인구합계_lag1"] = group_df["생활인구합계"].shift(1)
data_df["전체승객수_lag1"] = group_df["전체승객수"].shift(1)
data_df["아파트_평균_시가_lag1"] = group_df["아파트_평균_시가"].shift(1)

data_df['YEAR']     = data_df['YYYYMM'] // 100
data_df['MONTH']    = data_df['YYYYMM'] %  100
data_df['MONTH_SIN']= np.sin(2 * np.pi * data_df['MONTH'] / 12)
data_df['MONTH_COS']= np.cos(2 * np.pi * data_df['MONTH'] / 12)

cli_df = data_df.dropna()

# 정렬 다시 확인
cli_df = cli_df.sort_values(
    [ "YYYYMM","행정동코드"]
)


feat_df = cli_df[feat_cols]

feat_df.to_csv(rf"data/생활비용_학습용_202408_{now_date}_features.csv", index=False, encoding="utf-8-sig")

print('\n [결측치 확인]')
print(feat_df.isnull().sum())
print(len(feat_df))
print(feat_df.head(2))







