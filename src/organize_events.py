"""
Organize media files into event folders based on chat context and dates.

Creates folders:
  - media/events/2025-01-19_KHMC-Annual-Day/
  - media/events/2025-04-06_IAMV-Holi/
  - media/events/2026-02-08_CMB-Havan/
  - ... etc.
"""

import shutil
from pathlib import Path

# Mapping of specific dates to event names
EVENTS = {
    # Recitals & Concerts
    '2024-07-07': 'Student-Recital-Prep',
    '2024-07-21': 'Student-Recital-Jul2024',
    '2024-08-04': 'Independence-Day-Flag-Raising',
    '2024-10-11': 'Performance-Tix-Prep',
    '2024-10-26': 'Performance-Day',
    '2024-10-28': 'KHMC-Prep',
    '2024-05-20': 'iTablaPro-Setup',
    # KHMC
    '2025-01-19': 'KHMC-Annual-Day',
    '2025-06-21': 'KHMC-Dia-Performance',
    # Holi
    '2025-04-06': 'IAMV-Holi',
    '2025-04-07': 'IAMV-Holi-Photos',
    '2025-03-14': 'Holi-Mela',
    # Diwali
    '2025-10-12': 'Diwali-Mela-Prep',
    # CMB Havan
    '2026-02-08': 'CMB-Havan',
}

def organize_events():
    base_media = Path('media')
    events_dir = base_media / 'events'
    events_dir.mkdir(exist_ok=True)
    
    # Check all media subfolders
    for category in ['photos', 'video', 'audio']:
        cat_dir = base_media / category
        if not cat_dir.exists(): continue
        
        for file in cat_dir.iterdir():
            if file.is_dir(): continue
            
            # Extract date from filename (format: YYYY-MM-DD_...)
            parts = file.name.split('_')
            if not parts: continue
            file_date = parts[0]
            
            if file_date in EVENTS:
                event_name = EVENTS[file_date]
                event_folder = events_dir / f"{file_date}_{event_name}"
                event_folder.mkdir(exist_ok=True)
                
                # Copy or move? Let's copy for now to keep the categorized folders intact
                # but maybe moving is better for clean "Event" grouping.
                # User asked to "group by event", so let's move them to be definitive.
                target_path = event_folder / file.name
                shutil.move(file, target_path)
                print(f"Moved {file.name} to {event_folder.name}")

if __name__ == "__main__":
    organize_events()
