import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FOLDER = Path(os.getenv("PIGEON_FOLDER", "D:/Pigeon/PigeonReadable")).resolve()


def resolve(filename):
    # An absolute path like D:/Other/a.txt replaces FOLDER, so is_inside() catches it
    return (FOLDER / str(filename)).resolve()


def is_inside(filename):
    return FOLDER in resolve(filename).parents