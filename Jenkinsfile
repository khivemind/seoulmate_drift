pipeline {
    agent any

    triggers {
        cron('0 3 1 * *')
    }

    stages {
        
        stage('데이터 수집') {
            parallel {

                stage('한국은행 데이터 획득') {
                    steps {
                        dir('/home/ubuntu/seoulmate_drift') {
                            sh '''
                                venv/bin/python 한국은행데이터획득.py 2>&1 | tee logs/한국은행데이터획득.log
                            '''
                        }
                    }
                }
        
                stage('서울시 데이터 수집') {
                    steps {
                        dir('/home/ubuntu/seoulmate_drift') {
                            sh '''
                                venv/bin/python 서울시데이터획득.py 2>&1 | tee logs/서울시데이터획득.log
                            '''
                        }
                    }
                }
    
            }
        }
        
        stage('데이터 보간') {
            parallel {
                stage('한국은행 데이터 보간') {
                    steps {
                        dir('/home/ubuntu/seoulmate_drift') {
                            sh '''
                                venv/bin/python 한국은행데이터보간.py 2>&1 | tee logs/한국은행데이터보간.log
                            '''
                        }
                    }
                }
                stage('서울시 데이터 일반 보간') {
                    steps {
                        dir('/home/ubuntu/seoulmate_drift') {
                            
                            sh '''
                                venv/bin/python 서울시데이터보간.py 2>&1 | tee logs/서울시데이터보간.log
                            '''

                        }
                    }
                }
                stage('서울시 데이터 매출 보간') {
                    steps {
                        dir('/home/ubuntu/seoulmate_drift') {
                            
                            sh '''
                                venv/bin/python 서울시데이터보간_매출.py 2>&1 | tee logs/서울시데이터보간_매출.log
                            '''

                        }
                    }
                }


            }
        }

        stage('전체 데이터 보간') {
            steps {
                dir('/home/ubuntu/seoulmate_drift') {
                    
                    sh '''
                        venv/bin/python 전체데이터_보간.py 2>&1 | tee logs/전체데이터_보간.log
                    '''
                    
                }
            }
        }


        stage('feature engineering') {
            steps {
                dir('/home/ubuntu/seoulmate_drift') {
                    
                    sh '''
                        venv/bin/python 피처_엔지니어링.py 2>&1 | tee logs/피처_엔지니어링.log
                    '''
                    
                }
            }
        }
        
        stage('데이터 재학습 및 이번달 예측') {
            steps {
                dir('/home/ubuntu/seoulmate_drift') {
                    
                    sh '''
                        venv/bin/python 재학습_및_이번달예측.py 2>&1 | tee logs/재학습_및_이번달예측.log
                    '''
                    
                }
            }
        }        

        stage('예측결과 운영서버 전송') {
            steps {
                dir('/home/ubuntu/seoulmate_drift') {
                    sh '''
                        venv/bin/python 예측결과서버전송.py 2>&1 | tee logs/예측결과서버전송.log
                    '''
                }
            }
        }
        
        stage('UX 서비스 재시작') {
            steps {
                sshagent(['seoulmate-ssh']) {
                    sh """
                        ssh -o StrictHostKeyChecking=no overlord@seoulmate.cloud '
                            cd ~/SeoulMate &&
                            cd server &&
                            
                            echo "[1] 서비스 재시작" &&
                            docker-compose down &&
                            docker-compose up -d --build &&
                            
                            echo "[2] 서비스 기동 대기" &&
                            sleep 10 &&
                            cd ~/SeoulMate/server &&
                            
                            echo "[3] 데이터 로딩" &&
                            source /home/overlord/venv/bin/activate &&
                            MONGO_URI=mongodb://localhost:27017 python load_data.py                          
                        '
                    """
                    
                    sh """
                        echo "[4] 헬스 체크"
                        sleep 5
                        curl -f http://seoulmate.cloud:8000/health || exit 1
                    """
                }
            }
        }

        
    }
}
