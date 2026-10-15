
from tools import read_notes, summarize_text, save_briefing

print("TEST 1: Read meeting notes")
print(read_notes())

print("\nTEST 2: Read a missing file")
print(read_notes("missing.txt"))

print("\nTEST 3: Summarize text")
print(summarize_text(
    "Meeting on Monday. Report due Friday.",
    1
))

print("\nTEST 4: Handle empty text")
print(summarize_text(""))


print("\nTEST 5: Save a briefing")
print(save_briefing(
    "This is a test briefing.",
    "outputs/test_briefing.txt"
))


from audit import log_event

print("\nTEST 6: Audit logger")
log_event("Test event: Jarvis audit logging works")
print("Audit event recorded.")
