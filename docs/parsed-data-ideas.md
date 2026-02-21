# How the Parsed WhatsApp Data Can Be Used

Once the chat is parsed into structured messages (date, time, sender, body), here are concrete ways to use it.

---

## 1. **Class dates & calendar**

- **Detect class dates** from teacher messages, e.g.:
  - “I will see the kiddos today at 12:15”
  - “Please come by 2:30”
  - “We have moved the performance to the 8th of February”
- **Build a list of class/event dates** and show them in a simple calendar view (week or month).
- **Reschedule/cancel** from phrases like “moved to”, “snow date”, “online at 3 pm”.

*Parser already gives you every message with date/time and sender; you can add a small “class date detector” that looks for these phrases in teacher messages.*

---

## 2. **Practice recordings in one place**

- **Collect all Google Drive links** from the chat (parser has `message.get_drive_links()`).
- Filter to **teacher-only** links so you get official practice recordings, not random shares.
- **List by date** so you can see “new recording on 1/26” and open the folder.
- Later: open links in browser or copy to a “Practice recordings” page in the app.

*Use: `[m for m in messages if m.is_from_teacher() and m.has_drive_link()]` then `m.get_drive_links()`.*

---

## 3. **Attendance**

- **Manual (MVP):** calendar view with checkboxes: “Kid attended on Jan 26?” and store the answers.
- **Auto-hints:** find replies like “Yes we will be there”, “We are here” near a class date and suggest “likely attended” for that family.
- **Who replied:** list of senders who confirmed for a given date (from message sender + date).

*Parser gives sender + date for every message; you can match dates to class dates and senders to kids/parents.*

---

## 4. **Fees**

- **Fees = (number of classes attended) × (fee per class).**
- Once attendance is stored (from §3), compute total per child or per family.
- Optional: mark “paid” and show balance.

*No new parsing needed; this uses class dates + attendance.*

---

## 5. **Event logistics (time, place, links)**

- **Time:** “class at 12:15”, “come by 2:30”, “3 pm”.
- **Place:** “OM center North Billerica”, “parking behind the building”, “auditorium upstairs”.
- **Links:** Google Meet / FaceTime / Zoom in message body; extract and show “Join class” for that day.

*Same messages you use for class dates; add simple keyword extraction or a small list of phrases.*

---

## 6. **Search & reminders (later)**

- **Search:** “Show all messages about Brindavani Sarang” → search in `message.body` (and optionally sender/date).
- **Reminders:** “Remind me to practice before the next class” using next class date from §1.

*Parser already gives you a list of `Message` objects you can filter and search.*

---

## Suggested order

1. **Run the parser** on your zip and confirm message count and a few dates.
2. **Extract class dates** from teacher messages (keywords + date of message).
3. **Extract practice links** and list them by date.
4. **Simple calendar view** (dates + “recordings” link).
5. Add **attendance** (manual first) and **fees**.

The parser is the foundation; everything above builds on the same `Message` list.
