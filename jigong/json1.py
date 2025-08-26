import json


new_employee = {'firstName':'Zara','lastName': 'Araz'}

with open("exjson.json", "r", encoding="utf8") as f:
    data = json.load(f)   

data["employees"].append(new_employee)
 
with open("exjson.json", "w", encoding="utf8") as f:
    json.dump(data,f,indent=4)                    # 파일내용읽어오기

print("추가된 직원 리스트: ")
for emp in data["employees"]:
    print(emp)   
