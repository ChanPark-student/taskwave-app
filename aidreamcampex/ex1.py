#df는 age, sex, region, charges 열을 포함합니다.
#30 세 이상 고객만 남기고, sex 별 평균 charges를 계산하세요.
#결과는 컬럼 순서가 sex, mean_charges 인 DataFrame으로, mean_charges 내림차순으로 정렬해 반환하세요.

import pandas as pd

def problem1(df):
    answer = (
    df.loc[df["age"] >= 30]                 # ① 나이 필터
        .groupby("sex", as_index=False)["charges"].mean()                    # ③ 평균 계산
        .rename(columns={"charges": "mean_charges"})
        .sort_values("mean_charges", ascending=False)
        .reset_index(drop=True)               # ④ 인덱스 리셋
)
    return answer      # <- DataFrame(columns=['sex', 'mean_charges'])

"""
1. df.loc[df["age"] >= 32]
loc는 라벨(행/열)기반 인덱싱 메서드, 대괄호안 조건이 True인 행만 남긴다
df["age"] -> 불리언 시리즈 생성
#왜 불리언 시리즈를 만들고 대소비교를 해야하는지?

2. .groupby("sex", as_index=False)
gruopby는 같은 값을 가진 행끼리 묶어 집계를 준비한다.
"sex" 컬럼으로 그룹화,
as_index=False면 기본 인덱스를 유지하고, "sex"컬럼이 일반컬럼으로
#그럼 True면 sex컬럼이 인덱스 컬럼으로 변하는건지? 그럼 어떻게 되는건지?

3. ["charges"].mean()      
대괄호 하나 -> 시리즈 슬라이싱  
"charges"컬럼에 대해 평균 집계를 수행 / groupby와 함께 사용하면 그룹별 평균이 자동계산
# 평균 집계는 어떤 컬럼로우에서 나타나는건지?

4. .rename(columns={"charges": "mean_charges"})
컬럼 이름을 일괄 변경한다 .rename(columns={old:new})형태

5. .sort_values("mean_charges", ascending=False)
mean_charges 컬럼을 기준으로 내림차순 정렬

6. reset_index(drop = True)
인덱스가 그룹값으로 남거나 정렬로 뒤섞이므로 0부터 재부여
drop = True로 기존 인덱스열을 버리고 새로 생성


"""
