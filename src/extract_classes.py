"""
Extract class dates from parsed WhatsApp messages.

Looks for teacher messages that indicate a class is happening:
- "I will see the kiddos" / "see you" / "class at"
- Meeting links (FaceTime, Google Meet, Zoom)
- "come by [time]"
- Performance/event mentions with dates

Usage:
  python extract_classes.py path/to/chat.zip
  python extract_classes.py path/to/chat.txt
"""

import re
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from parse_whatsapp import parse_messages, Message


# Patterns that indicate a class or event is happening
CLASS_INDICATORS = [
    r"see the kiddos",
    r"see you (all|today|tomorrow|sunday|saturday)",
    r"class (at|is|will be|today|tomorrow)",
    r"come by \d",           # "come by 2:30"
    r"meet\.google\.com",    # Google Meet link
    r"facetime\.apple\.com", # FaceTime link
    r"zoom\.(us|com)",       # Zoom link
    r"practice (at|today|tomorrow)",
]

# Patterns that indicate date changes or cancellations
RESCHEDULE_PATTERNS = [
    r"moved.*(to|for).*(\d{1,2}(st|nd|rd|th)?(\s+of)?\s+\w+|\d{1,2}/\d{1,2})",
    r"rescheduled.*(to|for)",
    r"cancelled",
    r"no class",
    r"class.*cancelled",
]

# Patterns that indicate a performance/event
EVENT_PATTERNS = [
    r"performance",
    r"concert",
    r"event",
    r"havan",
    r"annual day",
]


@dataclass
class ClassDate:
    """A detected class or event."""
    date: str                    # e.g. "2/1/2026"
    time: str | None             # e.g. "12:15" if mentioned
    class_type: str              # "class", "online", "performance", "cancelled"
    evidence: str                # The message text that indicated this
    message_datetime: datetime   # When the message was sent


def _compile_patterns(patterns: list[str]) -> re.Pattern:
    """Combine patterns into one regex (case-insensitive)."""
    combined = "|".join(f"({p})" for p in patterns)
    return re.compile(combined, re.IGNORECASE)


CLASS_REGEX = _compile_patterns(CLASS_INDICATORS)
RESCHEDULE_REGEX = _compile_patterns(RESCHEDULE_PATTERNS)
EVENT_REGEX = _compile_patterns(EVENT_PATTERNS)

# Extract time like "12:15", "2:30", "3 pm"
TIME_REGEX = re.compile(r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b", re.IGNORECASE)


def extract_time_from_text(text: str) -> str | None:
    """Try to extract a time mention from text."""
    match = TIME_REGEX.search(text)
    return match.group(1) if match else None


def detect_class_type(body: str) -> str:
    """Determine what kind of class/event this is."""
    body_lower = body.lower()
    
    if RESCHEDULE_REGEX.search(body):
        if "cancel" in body_lower:
            return "cancelled"
        return "rescheduled"
    
    if "online" in body_lower or "facetime" in body_lower or "meet.google" in body_lower:
        return "online"
    
    if EVENT_REGEX.search(body):
        return "performance"
    
    return "class"


def extract_classes(messages: list[Message], teacher_name: str = "Vaishnavi") -> list[ClassDate]:
    """
    Extract class dates from messages.
    
    Looks at teacher messages for indicators that a class is happening.
    Returns a list of ClassDate objects sorted by date.
    """
    classes: list[ClassDate] = []
    seen_dates: set[str] = set()  # Avoid duplicates for same date
    
    for msg in messages:
        # Only look at teacher messages
        if not msg.is_from_teacher(teacher_name):
            continue
        
        body = msg.body
        
        # Check if this message indicates a class
        if not CLASS_REGEX.search(body) and not EVENT_REGEX.search(body):
            continue
        
        class_type = detect_class_type(body)
        time_mentioned = extract_time_from_text(body)
        
        # Use the message date as the class date
        # (Teacher usually sends these on the day of or day before class)
        class_date = msg.date
        
        # Skip if we already have this date (keep first mention)
        if class_date in seen_dates and class_type not in ("cancelled", "rescheduled"):
            continue
        
        seen_dates.add(class_date)
        
        classes.append(ClassDate(
            date=class_date,
            time=time_mentioned,
            class_type=class_type,
            evidence=body[:100] + ("..." if len(body) > 100 else ""),
            message_datetime=msg.datetime,
        ))
    
    # Sort by date
    classes.sort(key=lambda c: c.message_datetime)
    return classes


def strip_special_chars(text: str) -> str:
    """Remove non-ASCII chars for clean terminal output."""
    return text.encode("ascii", errors="ignore").decode("ascii")


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extract_classes.py <path to .zip or .txt>")
        sys.exit(1)

    path = Path(sys.argv[1])
    
    # Import and use the parser
    try:
        messages = parse_messages(path)
    except Exception as e:
        print(f"Error parsing: {e}")
        sys.exit(1)

    print(f"Parsed {len(messages)} messages.\n")
    
    classes = extract_classes(messages)
    
    print(f"Found {len(classes)} class/event dates:\n")
    print("-" * 70)
    
    for c in classes:
        time_str = f" at {c.time}" if c.time else ""
        print(f"  {c.date}{time_str}  [{c.class_type.upper()}]")
        print(f"    Evidence: \"{strip_special_chars(c.evidence)}\"")
        print()
    
    # Summary by type
    print("-" * 70)
    print("Summary:")
    by_type: dict[str, int] = {}
    for c in classes:
        by_type[c.class_type] = by_type.get(c.class_type, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")


if __name__ == "__main__":
    main()
