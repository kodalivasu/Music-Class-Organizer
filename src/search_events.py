from pathlib import Path
from parse_whatsapp import parse_messages
import re

zips = [
    Path('data/whatsapp-export/WhatsApp Chat - Hindustani Music Class at Chinmaya .zip'),
    Path('data/whatsapp-export/WhatsApp Chat - Kiddo Music Group .zip')
]

keywords = {
    'Diwali': r'diwali|deepavali',
    'Holi': r'holi',
    'Independence Day': r'independence|august 15|aug 15',
    'KHMC': r'khmc',
    'CMB Havan': r'cmb|havan',
    'Annual Day': r'annual day',
    'Concert/Performance': r'concert|performance'
}

for zp in zips:
    if not zp.exists(): continue
    print(f"\nSearching {zp.name}...")
    messages = parse_messages(zp)
    for msg in messages:
        for event, pattern in keywords.items():
            if re.search(pattern, msg.body, re.IGNORECASE):
                print(f"  [{msg.date}] {event}: {msg.body[:100]}...")
