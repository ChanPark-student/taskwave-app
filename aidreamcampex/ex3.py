import pandas as pd

def ex3(df):
    mask = (
        (df['age'] >= 30)&
        (df['smoker'] == 'yes')&
        (df['region'] == "southeast")
    )

    ans = df.loc[mask].copy()
    return ans

"""
mask는 boolean 1차원 (df와 크기가 같은)배열이다

df.loc[mask]는 mask가 true인 loc인덱스 행만 반환
한다는 뜻이다.
"""