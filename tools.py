
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


def summarize_text(text, max_sentences=3):
    if text.strip() == "":
        return failure("Text cannot be empty.")

    sentences = text.split(".")
    clean_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()

        if sentence != "":
            clean_sentences.append(sentence)

    summary = ". ".join(clean_sentences[:max_sentences])

    if summary != "":
        summary = summary + "."

    return success(summary)


result = read_notes()

print("\nFULL NOTES:")
print(result)

print("\nSUMMARY:")
print(summarize_text(
    "Meeting on Monday. Report due Friday. Test on Saturday. Submit on Sunday.",
    2
))

