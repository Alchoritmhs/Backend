import json
import pathlib
import pickle


def inin_pkl():
    if not pathlib.Path("data").exists():
        pathlib.Path("data").mkdir(parents=True, exist_ok=True)
    if not pathlib.Path('data/db.pkl').exists():
        rewriteFile('data/db.pkl', {'users': {}, 'files': {}})


def readFile(path):
    if ".pkl" in path:
        return pickle.load(open(path, 'rb'))
    else:
        with open(path, "r", encoding="utf-8") as file:
            if ".json" in path:
                try:
                    return json.load(file)
                except json.decoder.JSONDecodeError:
                    return ""
            if ".txt" in path:
                return file.read()


def rewriteFile(path, data):
    if '.pkl' in path:
        with open(path, 'wb') as file:
            pickle.dump(data, file)
    else:
        with open(path, "w") as file:
            file.write(data)
