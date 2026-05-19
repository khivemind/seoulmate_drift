import paramiko

# 접속 정보
hostname = "34.81.221.132"
username = "overlord"
pem_file = "overlord.pem"

local_file = f"data/도시활력지수.csv"
remote_file = f"/home/overlord/data/도시활력지수.csv"

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
