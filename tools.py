
def success(data):
    return {
        "success": True,
        "output": data,
        "error": None
    }


def failure(message):
    return {
        "success": False,
        "output": None,
        "error": message
    }


import os

def read_notes():
    filepath = "sample_data/meeting_notes.txt"

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()

        return success(content)

    except FileNotFoundError:
        return failure("Meeting notes file not found.")


print(read_notes())

