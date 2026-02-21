"""
Combine multiple WhatsApp chat exports into one analysis.

Usage:
  python combine_chats.py file1.zip file2.zip ...
  python combine_chats.py data/whatsapp-export/*.zip
"""

import sys
from pathlib import Path
from parse_whatsapp import parse_messages, Message
from extract_classes import extract_classes, strip_special_chars


def combine_messages(paths: list[Path]) -> list[Message]:
    """
    Parse and combine messages from multiple chat exports.
    Removes duplicates based on date+time+sender+body.
    """
    all_messages: list[Message] = []
    seen: set[tuple] = set()
    
    for path in paths:
        print(f"Parsing: {path.name}")
        try:
            messages = parse_messages(path)
            print(f"  Found {len(messages)} messages")
            
            added = 0
            for msg in messages:
                # Create a key for deduplication
                key = (msg.date, msg.time, msg.sender.lower(), msg.body[:100])
                if key not in seen:
                    seen.add(key)
                    all_messages.append(msg)
                    added += 1
            
            print(f"  Added {added} new (after dedup)")
        except Exception as e:
            print(f"  Error: {e}")
    
    # Sort by datetime
    all_messages.sort(key=lambda m: m.datetime)
    return all_messages


def main():
    if len(sys.argv) < 2:
        print("Usage: python combine_chats.py <file1.zip> <file2.zip> ...")
        print("Example: python combine_chats.py data/whatsapp-export/*.zip")
        sys.exit(1)
    
    paths = [Path(p) for p in sys.argv[1:]]
    
    # Filter to existing files
    valid_paths = [p for p in paths if p.exists()]
    if not valid_paths:
        print("No valid files found.")
        sys.exit(1)
    
    print(f"\nCombining {len(valid_paths)} chat exports...\n")
    print("=" * 60)
    
    messages = combine_messages(valid_paths)
    
    print("=" * 60)
    print(f"\nTotal: {len(messages)} unique messages")
    
    if messages:
        print(f"Date range: {messages[0].date} to {messages[-1].date}")
    
    # Teacher stats
    teacher = "Vaishnavi"
    from_teacher = [m for m in messages if m.is_from_teacher(teacher)]
    print(f"From teacher ({teacher}): {len(from_teacher)} messages")
    
    # Extract classes
    print("\n" + "=" * 60)
    print("EXTRACTED CLASS DATES")
    print("=" * 60 + "\n")
    
    classes = extract_classes(messages)
    
    for c in classes:
        time_str = f" at {c.time}" if c.time else ""
        print(f"  {c.date}{time_str}  [{c.class_type.upper()}]")
        print(f"    \"{strip_special_chars(c.evidence)[:80]}...\"")
        print()
    
    print("-" * 60)
    print("Summary:")
    by_type: dict[str, int] = {}
    for c in classes:
        by_type[c.class_type] = by_type.get(c.class_type, 0) + 1
    for t, count in sorted(by_type.items()):
        print(f"  {t}: {count}")
    
    print(f"\nTotal class/event dates: {len(classes)}")


if __name__ == "__main__":
    main()
