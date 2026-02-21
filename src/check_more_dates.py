from pathlib import Path
from parse_whatsapp import parse_messages
import re

zips = [
    Path('data/whatsapp-export/WhatsApp Chat - Hindustani Music Class at Chinmaya .zip'),
    Path('data/whatsapp-export/WhatsApp Chat - Kiddo Music Group .zip')
]

target_dates = ['5/20/24', '10/11/24', '3/13/25', '4/7/25', '10/12/25']

for zp in zips:
    if not zp.exists(): continue
    messages = parse_messages(zp)
    for msg in messages:
        if any(d in msg.date for d in target_dates):
             print(f"[{msg.date}] {msg.sender}: {msg.body[:200]}")
