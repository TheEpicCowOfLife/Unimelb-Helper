import json

def load_subjects(path = "data/subjects.json"):
    with open(path) as f:
        subjects = json.load(f)
        return subjects

def dump_subjects(subjects, path = "data/subjects.json"):
    with open(path,"w") as f:
        f.write(json.dumps(subjects, indent = 4))