import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def read_file(path: str):
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def load_specs():
    """
    Loads the core system prompt from the specs folder.
    """
    behaviour = read_file(os.path.join(BASE_DIR, "../specs/behaviour.md"))
    identity = read_file(os.path.join(BASE_DIR, "../specs/identity.md"))
    project = read_file(os.path.join(BASE_DIR, "../specs/project.md"))
    environment = read_file(os.path.join(BASE_DIR, "../specs/environment.md"))
    drift = read_file(os.path.join(BASE_DIR, "../specs/drift_protocol.md"))
    audio = read_file(os.path.join(BASE_DIR, "../specs/audio.md"))

    return "\n\n".join([
        behaviour,
        identity,
        project,
        environment,
        drift,
        audio
    ])

def load_repo_context():
    """
    Loads additional repo-anchored context (goals, subgoals, etc.)
    """
    goal = read_file(os.path.join(BASE_DIR, "../goals/main_goal.md"))
    subgoal = read_file(os.path.join(BASE_DIR, "../goals/subgoals.md"))

    return "\n\n".join([goal, subgoal])

