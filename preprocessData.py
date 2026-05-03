import re
import json 
pattern = r"\[(\d{2}/\d{2}/\d{2}), (\d{1,2}:\d{2}:\d{2})\s*(AM|PM)\] (.*?): (.*)"

data =[]
current = None

with open("chat.txt","r",encoding="utf-8") as f:
    for line in f:
        m = re.match(pattern,line)
        if m:
            if current:
                data.append(current)
            date,time,ampm,sender,message = m.groups()
            current = {"date":date,
                "time":f"{time} {ampm}",
                "sender":sender,
                "message":message
                }
        else:
            if current: 
                current["message"] += " " + line.strip()
                
if current:
    data.append(current)

for i in range(5):
    print(data[i])

skip = {"missed voice call", "missed video call", "deleted this message", "this message was deleted", "#include", "omitted", "Voice call","Video call","import","<!DOCTYPE html>","int main"}
data = [d for d in data if not any(s in d["message"].lower() for s in skip)]

with open("chats.jsonl","w") as f:
    for i in data:
        f.write(json.dumps(i))
        f.write("\n")

print(f"Total messages parsed: {len(data)}")