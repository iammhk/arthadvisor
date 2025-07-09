import json
from datetime import datetime

def add_global_advice(advice, author):
    """
    Add a new global advice entry to global_advice.json with author and timestamp.
    """
    entry = {
        "advice": advice,
        "author": author,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    try:
        with open("global_advice.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(entry)
    with open("global_advice.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Advice added.")

if __name__ == "__main__":
    advice = input("Enter advice: ")
    author = input("Enter author name: ")
    add_global_advice(advice, author)
