"""
One-off migration: move existing shared media into tenant directories for teacher_id 1.

Run from project root: python scripts/migrate_media_to_tenant_dirs.py

- media/audio/*  -> media/audio/1/
- media/events/* -> media/events/1/  (each event folder becomes media/events/1/EventName/)
- media/photos/* -> media/photos/1/

Skips if target dir already has content or source is empty. Safe to run multiple times.
"""

import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MEDIA = BASE / "media"


def migrate_audio():
    audio_root = MEDIA / "audio"
    target = MEDIA / "audio" / "1"
    if not audio_root.exists():
        return
    files = [f for f in audio_root.iterdir() if f.is_file()]
    if not files:
        return
    target.mkdir(parents=True, exist_ok=True)
    for f in files:
        dest = target / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))
            print(f"  audio: {f.name} -> audio/1/")
    print(f"  Migrated {len(files)} audio file(s) to media/audio/1/")


def migrate_events():
    events_root = MEDIA / "events"
    target_dir = MEDIA / "events" / "1"
    if not events_root.exists():
        return
    subdirs = [d for d in events_root.iterdir() if d.is_dir() and d.name != "1"]
    if not subdirs:
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for d in subdirs:
        dest = target_dir / d.name
        if not dest.exists():
            shutil.move(str(d), str(dest))
            print(f"  events: {d.name} -> events/1/")
    print(f"  Migrated {len(subdirs)} event folder(s) to media/events/1/")


def migrate_photos():
    photos_root = MEDIA / "photos"
    target = MEDIA / "photos" / "1"
    if not photos_root.exists():
        return
    files = [f for f in photos_root.iterdir() if f.is_file()]
    if not files:
        return
    target.mkdir(parents=True, exist_ok=True)
    for f in files:
        dest = target / f.name
        if not dest.exists():
            shutil.move(str(f), str(dest))
            print(f"  photos: {f.name} -> photos/1/")
    print(f"  Migrated {len(files)} photo(s) to media/photos/1/")


def main():
    print("Migrating media to tenant dirs (teacher_id=1)...")
    migrate_audio()
    migrate_events()
    migrate_photos()
    print("Done.")


if __name__ == "__main__":
    main()
