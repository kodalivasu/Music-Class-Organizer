from pathlib import Path
from parse_whatsapp import parse_messages
import re

zips = [
    Path('data/whatsapp-export/WhatsApp Chat - Hindustani Music Class at Chinmaya .zip'),
    Path('data/whatsapp-export/WhatsApp Chat - Kiddo Music Group .zip')
]

for zp in zips:
    if not zp.exists(): continue
    messages = parse_messages(zp)
    for msg in messages:
        if re.search(r'independence|august 15|aug 15', msg.body, re.IGNORECASE):
             print(f"[{msg.date}] {msg.sender}: {msg.body[:200]}")
