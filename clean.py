import json

INPUT  = "chats.jsonl"
OUTPUT = "chats_clean.jsonl"

# patterns that mark a system/event message (lowercase match)
SKIP_PATTERNS = [
    "voice call",
    "video call",
    "missed voice call",
    "missed video call",
    "click to call back",
    "no answer",
    "this message was deleted",
    "deleted this message",
    "you deleted this message",
    "\u200e",          # left-to-right mark whatsapp puts on system msgs
    "messages and calls are end-to-end encrypted",
    "null",
]

def is_system(msg: str) -> bool:
    low = msg.strip().lower()
    return any(p in low for p in SKIP_PATTERNS)

kept = dropped = 0

with open(INPUT, encoding="utf-8") as fin, \
     open(OUTPUT, "w", encoding="utf-8") as fout:
    for line in fin:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            try:
                row = eval(line)
            except:
                continue

        if is_system(row.get("message", "")):
            dropped += 1
        else:
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")
            kept += 1

print(f"Done — kept {kept}, removed {dropped} system messages")
print(f"Clean file saved to: {OUTPUT}")