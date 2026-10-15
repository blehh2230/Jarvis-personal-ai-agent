from audit import log_event

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


def read_notes(filename="sample_data/meeting_notes.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as file:
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

def save_briefing(content, filepath="outputs/meeting_briefing.txt"):
    if content.strip() == "":
        return failure("Briefing content cannot be empty.")

    try:
        with open(filepath, "x", encoding="utf-8") as file:
            file.write(content)

        return success("Briefing saved successfully.")

    except FileExistsError:
        return failure("Briefing file already exists.")

    except OSError:
        return failure("Could not save the briefing.")


def create_briefing(output_path="outputs/meeting_briefing.txt"):
    log_event("Workflow started")

    print("Step 1: Reading notes...")
    log_event("Reading meeting notes: STARTED")
    notes_result = read_notes()

    if not notes_result["success"]:
        log_event("Reading meeting notes: FAILED")
        log_event("Workflow failed")
        return notes_result

    log_event("Reading meeting notes: SUCCESS")

    print("Step 2: Summarizing notes...")
    log_event("Summarizing notes: STARTED")
    summary_result = summarize_text(notes_result["output"], 3)

    if not summary_result["success"]:
        log_event("Summarizing notes: FAILED")
        log_event("Workflow failed")
        return summary_result

    log_event("Summarizing notes: SUCCESS")

    print("Step 3: Saving briefing...")
    log_event("Saving briefing: STARTED")
    save_result = save_briefing(
        summary_result["output"],
        output_path
    )

    if not save_result["success"]:
        log_event("Saving briefing: FAILED")
        log_event("Workflow failed")
        return save_result

    log_event("Saving briefing: SUCCESS")
    log_event("Workflow completed successfully")

    return success({
        "summary": summary_result["output"],
        "message": save_result["output"]
    })


if __name__ == "__main__":
    result = create_briefing()
    print("\nFINAL RESULT:")
    print(result)
    

