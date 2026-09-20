
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from specs_loader import load_specs
from specs_loader import load_repo_context

SYSTEM_PROMPT = load_specs() + "\n\n" + load_repo_context()



import time
import json
from fastapi import FastAPI, Request

LOG_FILE = "tasks/logs/agent.log"
MEMORY_FILE = "config/memory.json"
MESSAGE_FILE = "config/messages.json"
QUEUE_FILE = "config/queue.json"


agent_log = []
app = FastAPI()


from openai import OpenAI
client = OpenAI()

DEFAULT_MODEL = "gpt-5.4-mini"

def call_llm(user_message, model: str = DEFAULT_MODEL):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages
    )

    return response.choices[0].message.content


    return response.choices[0].message.content[0].text

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
        return {
            "profile": {},
            "catalogue": {}
        }

def save_memory(mem):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(mem, f, indent=2)
        return "Memory saved"
    except Exception as e:
        return f"Error saving memory: {e}"


def load_repo_context():
    goal = read_file("goals/main_goal.md")
    subgoal = read_file("goals/subgoals.md")
    identity = read_file("specs/identity.md")
    behaviour = read_file("specs/behaviour.md")
    drift = read_file("specs/drift_protocol.md")

    return "\n\n".join([goal, subgoal, identity, behaviour, drift])



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
# Task Queue
# -------------------------
def load_queue():
    try:
        with open(QUEUE_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_queue(q):
    try:
        with open(QUEUE_FILE, "w") as f:
            json.dump(q, f, indent=2)
        return "Queue saved"
    except Exception as e:
        return f"Error saving queue: {e}"

# -------------------------
# Core Tasks
# -------------------------
async def task_ping(request: Request):
    return "pong"

async def task_time(request: Request):
    return time.strftime("%Y-%m-%d %H:%M:%S")

async def task_readfile(request: Request):
    path = request.query_params.get("path")
    if not path:
        return "Error: 'path' parameter required"
    return read_file(path)

async def task_writefile(request: Request):
    path = request.query_params.get("path")
    content = request.query_params.get("content")
    if not path or content is None:
        return "Error: 'path' and 'content' parameters required"
    return write_file(path, content)

async def task_remember(request: Request):
    key = request.query_params.get("key")
    value = request.query_params.get("value")
    if not key or value is None:
        return "Error: 'key' and 'value' required"
    mem = load_memory()
    mem[key] = value
    save_memory(mem)
    return {"stored": {key: value}}

async def task_recall(request: Request):
    key = request.query_params.get("key")
    if not key:
        return "Error: 'key' required"
    mem = load_memory()
    value = mem.get(key, None)
    return {"key": key, "value": value}

async def task_memory_all(request: Request):
    return load_memory()

async def task_send_message(request: Request):
    to_agent = request.query_params.get("to")
    from_agent = request.query_params.get("from")
    msg = request.query_params.get("msg")

    if not to_agent or not from_agent or msg is None:
        return "Error: 'to', 'from', and 'msg' required"

    msgs = load_messages()
    if to_agent not in msgs:
        msgs[to_agent] = []
    msgs[to_agent].append({"from": from_agent, "msg": msg})
    save_messages(msgs)
    return {"sent_to": to_agent, "message": msg}

async def task_get_messages(request: Request):
    agent = request.query_params.get("agent")
    if not agent:
        return "Error: 'agent' required"
    msgs = load_messages()
    return msgs.get(agent, [])

async def task_clear_messages(request: Request):
    agent = request.query_params.get("agent")
    if not agent:
        return "Error: 'agent' required"
    msgs = load_messages()
    msgs[agent] = []
    save_messages(msgs)
    return {"cleared": agent}

async def task_list_agents(request: Request):
    msgs = load_messages()
    return list(msgs.keys())

async def task_list_tasks(request: Request):
    return sorted(TASKS.keys())

# -------------------------
# Queue Tasks
# -------------------------
async def task_enqueue_task(request: Request):
    task_name = request.query_params.get("task")
    if not task_name:
        return "Error: 'task' parameter required"

    params = {k: v for k, v in request.query_params.items() if k != "task"}

    q = load_queue()
    entry = {"task": task_name, "params": params}
    q.append(entry)
    save_queue(q)

    return {"queued": entry}

async def task_dequeue_task(request: Request):
    q = load_queue()
    if not q:
        return {"task": None}

    entry = q.pop(0)
    save_queue(q)
    return entry

# -------------------------
# Profile Tasks
# -------------------------
async def task_set_profile_pref(request: Request):
    key = request.query_params.get("key")
    value = request.query_params.get("value")
    if not key or value is None:
        return "Error: 'key' and 'value' required"

    mem = load_memory()
    mem.setdefault("profile", {})
    mem["profile"][key] = value
    save_memory(mem)

    return {"profile_updated": {key: value}}

async def task_get_profile(request: Request):
    mem = load_memory()
    return mem.get("profile", {})

# -------------------------
# Catalogue Tasks (with fix)
# -------------------------
async def task_add_track(request: Request):
    track = request.query_params.get("track")
    if not track:
        return "Error: 'track' parameter required"

    params = {
        k: v for k, v in request.query_params.items()
        if k not in ["name", "track"]
    }

    mem = load_memory()
    mem.setdefault("catalogue", {})
    mem["catalogue"][track] = params
    save_memory(mem)

    return {"track_added": {track: params}}

async def task_list_tracks(request: Request):
    mem = load_memory()
    return mem.get("catalogue", {})

async def task_update_track(request: Request):
    track = request.query_params.get("track")
    if not track:
        return "Error: 'track' required"

    mem = load_memory()
    if track not in mem.get("catalogue", {}):
        return {"error": "Track not found"}

    updates = {
        k: v for k, v in request.query_params.items()
        if k not in ["name", "track"]
    }

    mem["catalogue"][track].update(updates)
    save_memory(mem)

    return {"track_updated": {track: mem["catalogue"][track]}}

# -------------------------
# Task Registry
# -------------------------
TASKS = {
    "ping": task_ping,
    "time": task_time,
    "readfile": task_readfile,
    "writefile": task_writefile,
    "remember": task_remember,
    "recall": task_recall,
    "memory_all": task_memory_all,
    "send_message": task_send_message,
    "get_messages": task_get_messages,
    "clear_messages": task_clear_messages,
    "list_agents": task_list_agents,
    "list_tasks": task_list_tasks,
    "enqueue_task": task_enqueue_task,
    "dequeue_task": task_dequeue_task,
    "set_profile_pref": task_set_profile_pref,
    "get_profile": task_get_profile,
    "add_track": task_add_track,
    "list_tracks": task_list_tracks,
    "update_track": task_update_track,
}

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

    if not name:
        result = "Error: 'name' parameter required"
    elif name in TASKS:
        handler = TASKS[name]
        result = await handler(request)
    else:
        result = f"Unknown task: '{name}'"

    log(f"Completed task: {name}")
    return {"task": name, "result": result}


def run_terminal_agent():
    print("Agent ready. Type your message:")

    while True:
        user_input = input("You: ")

        reply = call_llm(user_input)

        print("Agent:", reply)


if __name__ == "__main__":
    run_terminal_agent()

