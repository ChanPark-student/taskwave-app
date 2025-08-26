"""
df에는 user_id, signup_date, last_login_date가 
YYYY-MM-DD 문자열로 주어집니다.

가입일부터 30 일 이내 한 번이라도 로그인한 유저를 ‘retained’라 정의합니다.

월별(가입월) 리텐션 비율 = retained_user / total_signup 을 계산하여,
month 열과 retention_rate 열(소수점 2자리)만 
가진 DataFrame으로 오름차순 반환하세요.
"""
import pandas as pd

def problem2(df):
    
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    df["last_login_date"] = pd.to_datetime(df["last_login_date"])

    df["gap_days"] = (df["last_login_date"] - df["signup_date"]).dt.days
    df["retained"] = df["gap_days"] <= 30

    df['month'] = df['signup_date'].dt.to_period('M').astype(str)

    grouped = df.groupby('month')['retained'].agg(
        retention_rate = lambda x: round(x.mean(),2)
    ).reset_index

    return grouped

"""
pd.to_datetime(...):	문자열을 날짜형으로 변환
(date2 - date1).dt.days:    날짜 차이를 정수(일 단위)로 계산
df["col"] <= 30:	불리언 조건으로 새로운 컬럼 생성
dt.to_period("M").astype(str):    날짜를 ‘2025-01’ 같은 월 단위 문자열로 추출
.groupby(...).agg(...):   그룹별 평균 또는 사용자 지정 집계 수행
"""
