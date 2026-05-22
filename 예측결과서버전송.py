import paramiko
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import chardet

# 전송용 파일 생성
edm_mapping_df = pd.read_csv(rf"data/서울시_행정동ID_행정동코드_맵핑_base.csv", encoding="utf-8-sig")
data_df = pd.read_csv(rf"data/생활비용지수_score.csv", encoding="utf-8-sig")

data_df["생활비용지수_등급"] = pd.cut(
    data_df["생활비용지수"],
    bins=5,              # min~max 자동 5등분
    labels=[5,4,3,2,1],
    include_lowest=True
)

data_df["생활비용지수"] = (
    ((data_df["생활비용지수"] - 6) / 6) * 100
).round(2)

data_df['년도']     = data_df['YYYYMM'] // 100
data_df['월']    = data_df['YYYYMM'] %  100

merge_df = pd.merge(
    data_df,
    edm_mapping_df,
    on="행정동코드",
    how="left"
)

new_df = merge_df[["YYYYMM","행정동코드","년도","월","행정동_명칭","자치구_명칭","생활비용지수_등급","생활비용지수"]]

merge_df.sort_values(by=["YYYYMM","행정동코드"], inplace=True)

new_df.to_csv(rf"data/도시활력지수.csv", index=False, encoding="utf-8-sig")

# 접속 정보
hostname = "34.81.221.132"
username = "overlord"
pem_file = "overlord.pem"

local_file = f"data/도시활력지수.csv"
remote_file = f"/home/overlord/SeoulMate/server/data/expenses_model.csv"

# SSH 키 로드
key = paramiko.RSAKey.from_private_key_file(pem_file)

# SSH 연결
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(
        hostname=hostname,
        username=username,
        pkey=key
    )

    print(f"{hostname} 서버 접속")

    # SFTP 시작
    sftp = ssh.open_sftp()

    # 업로드
    sftp.put(local_file, remote_file)

    print("파일 전송 완료")

except Exception as e:
    print(f"오류: {e}")

finally:
    sftp.close()
    ssh.close()
