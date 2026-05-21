# 1. import
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from lightgbm import LGBMRegressor
from lightgbm import early_stopping, log_evaluation
import chardet
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os


# 지금 시간
start_date = 202408
dt = datetime.today() - relativedelta(months=1)
previous_date = dt.year * 100 + dt.month     # 오늘 기준 이전달

dt = datetime.today()
now_date =  dt.year * 100 + dt.month      # 이번달

# 10% 되는 위치 찾기
start = pd.to_datetime(str(start_date), format="%Y%m").to_period("M")
end = pd.to_datetime(str(start_date), format="%Y%m").to_period("M")

months = (end.year - start.year) * 12 + (end.month - start.month) + 1
offset = int(months * 0.1)
result = end - offset

pivot_date = int(result.strftime("%Y%m"))

#
#   전처리된 데이터
#

data_name = rf"data/생활비용_학습용_202408_{now_date}_features.csv"
feat_df = pd.read_csv(data_name, encoding="utf-8-sig")

print(f"{data_name}의 item 갯수 {len(feat_df)}")
print(feat_df.head(2))

#3. 데이터 전처리
print('\n [결측치 확인]')
print(feat_df.isnull().sum())

# 데이터 분할
# 시계열로 분할

cost_index = "생활비용지수"

train_df = feat_df[(feat_df["YYYYMM"] >= 202411) & (feat_df["YYYYMM"] <= 202501)]
valid_df = feat_df[(feat_df["YYYYMM"] >= 202602) & (feat_df["YYYYMM"] <= 202604)]
test_df = feat_df[(feat_df["YYYYMM"] >= 202605) & (feat_df["YYYYMM"] <= 202605)]

X_train = train_df.drop(columns=cost_index)
y_train = train_df[cost_index]

X_valid = valid_df.drop(columns=cost_index)
y_valid = valid_df[cost_index]


X_test = test_df.drop(columns=cost_index)
y_test = test_df[cost_index]


#display(X_train.head(2))
print("train:", X_train.shape)

print("valid:", X_valid.shape)


#display(X_test.head(2))
print("test:", X_test.shape)

print(f"train 기간: {X_train['YYYYMM'].min()} - {X_train['YYYYMM'].max()}")
print(f"valid 기간: {X_valid['YYYYMM'].min()} - {X_valid['YYYYMM'].max()}")
print(f"test  기간: {X_test['YYYYMM'].min()} - {X_test['YYYYMM'].max()}")




# 4. 모델 생성 및 학습 (LightGBM 모델)
model = LGBMRegressor(
    objective="regression",
    n_estimators=3000,  # 트리개수
    learning_rate=0.03,  # 학습률
    max_depth=-1,        # 트리 최대 깊이  (-1 제한없음)
    num_leaves=31,       # leaf 개수
    subsample=1.0,       # 데이터 샘플링 비율 (과적합 방지)
    colsample_bytree=0.9, # feature 샘플링 비율 (과적합 방지)
    random_state=42
)

model.fit(
    X_train,
    y_train,
    eval_set=[(X_valid, y_valid)],
    eval_metric="l1",
    categorical_feature=["행정동코드"],
    callbacks=[
        early_stopping(stopping_rounds=100),
        log_evaluation(period=100)
    ]
)


# 모델 학습
model.fit(X_train, y_train)    # leaf-wise 방식 학습

# 5. 예측 수행
y_pred = model.predict(X_test)


# 6. 성능 평가
# MAE
mae = mean_absolute_error(y_test, y_pred)

# RMSE
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

# R2  <- 모델 설명력 (1에 가까울수록 좋은)
r2 = r2_score(y_test, y_pred)

# 결과 출력
print('\n [LightGBM 성능]')
print(f"MAE : {mae:.4f}")
print(f"RMSE :{rmse:.4f}")
print(f"R2 : {r2:.4f}")

# 8. Feature Importance
importance = model.feature_importances_

# 중요도 정렬
indices = np.argsort(importance)

print(f"feature importances : {X_train.columns[indices]}")

# 9. 모델 예측
# 예측 수행
test_pred = model.predict(X_test)

print(f"\n [이번달 {now_date} 예측 결과]")
for i, pred in enumerate(test_pred):
    print(f"{X_test.iloc[i]['행정동코드']}번째 생활비용지수: {pred:.4f}")

X_test["생활비용지수"] = test_pred

this_month_df = X_test[["YYYYMM","행정동코드","생활비용지수"]]

#this_month_df.to_csv(rf"data/생활비용지수_{now_date}_score.csv", encoding="utf-8-sig", index=False)

data_df = feat_df[feat_df["YYYYMM"] != feat_df["YYYYMM"].max()]

data_df = pd.concat([data_df, this_month_df])

data_df = data_df[["YYYYMM","행정동코드","생활비용지수"]]

data_df.to_csv(rf"data/생활비용지수_score.csv", encoding="utf-8-sig", index=False)












