import time
import json
from fastapi import FastAPI, Request

LOG_FILE = "agent.log"
MEMORY_FILE = "memory.json"
MESSAGE_FILE = "messages.json"

agent_log = []
app = FastAPI()

# -------------------------
# Logging
# -------------------------
def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    agent_log.append(entry)

    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

    return entry

# -------------------------
# Structured Memory
# -------------------------
def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
        return "Memory saved"
    except Exception as e:
        return f"Error saving memory: {e}"

# -------------------------
# File Read / Write
# -------------------------
def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str):
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

# -------------------------
# Multi-Agent Messaging
# -------------------------
def load_messages():
    try:
        with open(MESSAGE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_messages(msgs):
    try:
        with open(MESSAGE_FILE, "w") as f:
            json.dump(msgs, f, indent=2)
        return "Messages saved"
    except Exception as e:
        return f"Error saving messages: {e}"

# -------------------------
# Routes
# -------------------------
@app.get("/")
async def root():
    return {"status": "agent online"}

@app.get("/log")
async def get_log():
    return {"log": agent_log}

@app.get("/task")
async def task(request: Request):
    name = request.query_params.get("name")
    log(f"Received task: {name}")

    # -------------------------
    # Built-in tasks
    # -------------------------
    if name == "ping":
        result = "pong"

    elif name == "time":
        result = time.strftime("%Y-%m-%d %H:%M:%S")

    # -------------------------
    # File tasks
    # -------------------------
    elif name == "readfile":
        path = request.query_params.get("path")
        if not path:
            result = "Error: 'path' parameter required"
        else:
            result = read_file(path)

    elif name == "writefile":
        path = request.query_params.get("path")
        content = request.query_params.get("content")
        if not path or content is None:
            result = "Error: 'path' and 'content' parameters required"
        else:
            result = write_file(path, content)

    # -------------------------
    # Structured Memory tasks
    # -------------------------
    elif name == "remember":
        key = request.query_params.get("key")
        value = request.query_params.get("value")
        if not key or value is None:
            result = "Error: 'key' and 'value' required"
        else:
            mem = load_memory()
            mem[key] = value
            save_memory(mem)
            result = {"stored": {key: value}}

    elif name == "recall":
        key = request.query_params.get("key")
        if not key:
            result = "Error: 'key' required"
        else:
            mem = load_memory()
            value = mem.get(key, None)
            result = {"key": key, "value": value}

    elif name == "memory_all":
        mem = load_memory()
        result = mem

    # -------------------------
    # Multi-Agent Messaging tasks
    # -------------------------
    elif name == "send_message":
        to_agent = request.query_params.get("to")
        from_agent = request.query_params.get("from")
        msg = request.query_params.get("msg")

        if not to_agent or not from_agent or msg is None:
            result = "Error: 'to', 'from', and 'msg' required"
        else:
            msgs = load_messages()
            if to_agent not in msgs:
                msgs[to_agent] = []
            msgs[to_agent].append({"from": from_agent, "msg": msg})
            save_messages(msgs)
            result = {"sent_to": to_agent, "message": msg}

    elif name == "get_messages":
        agent = request.query_params.get("agent")
        if not agent:
            result = "Error: 'agent' required"
        else:
            msgs = load_messages()
            result = msgs.get(agent, [])

    elif name == "clear_messages":
        agent = request.query_params.get("agent")
        if not agent:
            result = "Error: 'agent' required"
        else:
            msgs = load_messages()
            msgs[agent] = []
            save_messages(msgs)
            result = {"cleared": agent}

    elif name == "list_agents":
        msgs = load_messages()
        result = list(msgs.keys())

    # -------------------------
    # Default
    # -------------------------
    else:
        result = f"Task '{name}' processed"

    log(f"Completed task: {name}")
    return {"task": name, "result": result}


