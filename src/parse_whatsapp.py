"""
Parse WhatsApp chat export (zip or .txt) into structured messages.

Usage:
  python parse_whatsapp.py path/to/chat.zip
  python parse_whatsapp.py path/to/chat.txt

Handles multiple WhatsApp export formats:
  - Format A: [5:55 PM, 2/8/2026] sender: message   (time first, 4-digit year)
  - Format B: [7/17/23, 5:54:21 PM] sender: message (date first, 2-digit year)
"""

import re
import zipfile
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

# Unicode normalization: WhatsApp uses narrow no-break space (\u202f) before AM/PM
# and left-to-right mark (\u200e) at start of some messages
def _normalize(text: str) -> str:
    """Replace special Unicode spaces/marks with regular chars."""
    return text.replace("\u202f", " ").replace("\u200e", "").replace("\r", "")

# Format A: [5:55 PM, 2/8/2026] sender: message
# Time first, 4-digit year
FORMAT_A = re.compile(
    r"^\[(\d{1,2}:\d{2}\s*[AP]M),\s*(\d{1,2}/\d{1,2}/\d{4})\]\s*(.+?):\s*(.*)$",
    re.IGNORECASE,
)

# Format B: [7/17/23, 5:54:21 PM] sender: message  
# Date first, 2-digit year, optional seconds
FORMAT_B = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*[AP]M)\]\s*(.+?):\s*(.*)$",
    re.IGNORECASE,
)


@dataclass
class Message:
    """One WhatsApp message."""
    time: str       # e.g. "5:55 PM" or "5:55:21 PM"
    date: str       # e.g. "2/8/2026" or "7/17/23"
    sender: str     # e.g. "Vaishnavi  Kondapalli"
    body: str       # full message text (including multi-line)

    @property
    def datetime(self) -> datetime:
        """Parse to datetime for sorting/filtering."""
        # Remove seconds if present (e.g. "5:54:21 PM" -> "5:54 PM")
        # Pattern: hour:min:sec where :sec is right before AM/PM
        time_clean = re.sub(r"(\d{1,2}:\d{2}):\d{2}(\s*[AP]M)", r"\1\2", self.time, flags=re.IGNORECASE)
        
        s = f"{self.date} {time_clean}"
        
        # Try 4-digit year first, then 2-digit
        for fmt in ("%m/%d/%Y %I:%M %p", "%m/%d/%y %I:%M %p"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date/time: {s}")

    def is_from_teacher(self, teacher_name: str = "Vaishnavi") -> bool:
        return teacher_name.lower() in self.sender.lower()

    def has_drive_link(self) -> bool:
        return "drive.google.com" in self.body

    def get_drive_links(self) -> list[str]:
        """Extract Google Drive URLs from message body."""
        url_pattern = re.compile(
            r"https?://drive\.google\.com/[^\s<>'\"]+",
            re.IGNORECASE,
        )
        return url_pattern.findall(self.body)


def _read_lines(path: Path) -> Iterator[str]:
    """Yield lines from a .txt file, trying UTF-8 then Latin-1."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")


def _open_export(path: Path) -> tuple[Iterator[str], Path]:
    """
    Open export from zip or .txt.
    Returns (line_iterator, source_path).
    """
    path = Path(path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path, "r") as z:
            # WhatsApp exports the chat as "_chat.txt"
            names = z.namelist()
            chat_file = None
            
            # Prefer _chat.txt (WhatsApp's standard name)
            for n in names:
                if n.lower() == "_chat.txt":
                    chat_file = n
                    break
            
            # Fall back to any .txt file
            if not chat_file:
                txt_files = [n for n in names if n.lower().endswith(".txt")]
                if txt_files:
                    chat_file = txt_files[0]
            
            if not chat_file:
                raise ValueError("Zip has no chat .txt file inside")
            
            text = z.read(chat_file).decode("utf-8", errors="replace")
            lines = (line.rstrip("\n") for line in text.splitlines())
            return lines, path / chat_file
    else:
        return _read_lines(path), path


def _try_parse_line(line: str) -> Message | None:
    """Try to parse a line as a message start using both formats."""
    line = _normalize(line)
    
    # Try Format A: [TIME, DATE] sender: message
    m = FORMAT_A.match(line)
    if m:
        time_str, date_str, sender, body = m.groups()
        return Message(time=time_str.strip(), date=date_str.strip(), 
                       sender=sender.strip(), body=body)
    
    # Try Format B: [DATE, TIME] sender: message
    m = FORMAT_B.match(line)
    if m:
        date_str, time_str, sender, body = m.groups()
        return Message(time=time_str.strip(), date=date_str.strip(),
                       sender=sender.strip(), body=body)
    
    return None


def parse_messages(path: Path) -> list[Message]:
    """
    Parse WhatsApp export (zip or .txt) into a list of Message objects.
    Handles multi-line messages (lines that don't start with [ are merged).
    Supports multiple WhatsApp date formats.
    """
    lines_iter, _ = _open_export(path)
    messages: list[Message] = []
    current: Message | None = None

    for line in lines_iter:
        msg = _try_parse_line(line)
        if msg:
            current = msg
            messages.append(current)
        elif current is not None and line.strip():
            # continuation of previous message
            current.body += "\n" + _normalize(line)

    return messages


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python parse_whatsapp.py <path to .zip or .txt>")
        print("Example: python parse_whatsapp.py ../data/whatsapp-export/WhatsApp Chat - Kiddo Music Group .zip")
        sys.exit(1)

    path = Path(sys.argv[1])
    try:
        messages = parse_messages(path)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Parsed {len(messages)} messages.\n")

    # Quick stats
    teacher = "Vaishnavi"
    from_teacher = [m for m in messages if m.is_from_teacher(teacher)]
    with_links = [m for m in messages if m.has_drive_link()]

    print(f"  From teacher ({teacher}): {len(from_teacher)}")
    print(f"  With Google Drive links:  {len(with_links)}")

    if with_links:
        print("\n--- Practice recording links (from teacher) ---")
        for m in from_teacher:
            for url in m.get_drive_links():
                print(f"  {m.date}: {url[:70]}...")

    # Show first 3 and last 2 as sanity check
    print("\n--- First 3 messages ---")
    for m in messages[:3]:
        body_preview = (m.body[:60] + "…") if len(m.body) > 60 else m.body
        print(f"  [{m.date} {m.time}] {m.sender}: {body_preview}")

    print("\n--- Last 2 messages ---")
    for m in messages[-2:]:
        body_preview = (m.body[:60] + "…") if len(m.body) > 60 else m.body
        print(f"  [{m.date} {m.time}] {m.sender}: {body_preview}")


if __name__ == "__main__":
    main()
