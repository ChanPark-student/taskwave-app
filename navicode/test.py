import requests

url = "https://apis-navi.kakaomobility.com/v1/directions"
headers = {"Authorization": "KakaoAK a48662b4aef237389e8ecf140f3a5061"}
params = {
    "origin": "128.7711,35.4745",
    "destination": "128.6283,35.8793",
    "priority": "RECOMMEND",
    "car_fuel": "GASOLINE",
    "car_hipass": "false",
    "summary": "false",
    "alternatives": "false",
    "road_details": "false"
}

r = requests.get(url, headers=headers, params=params)
print(r.status_code, r.text)

