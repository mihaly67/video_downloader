import json
import datetime
import argparse
import os

MEMORY_FILE = "Knowledge_Base/agent_memory.jsonl"

def write_memory(category, content):
    if not os.path.exists("Knowledge_Base"):
        os.makedirs("Knowledge_Base")
    with open(MEMORY_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category,
            "content": content
        }) + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True)
    parser.add_argument("--category", default="General")
    parser.add_argument("--content", default="")
    args = parser.parse_args()

    if args.action == "write":
        write_memory(args.category, args.content)
