
from datetime import datetime

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("outputs/audit.log", "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] {message}\n")
