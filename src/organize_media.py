"""
Extract and organize media files from WhatsApp exports.

Creates folders:
  - media/audio/    (practice recordings, class audio)
  - media/video/    (class videos, performances)
  - media/photos/   (pictures)

Renames files with readable dates and context from chat messages.

Usage:
  python organize_media.py file1.zip file2.zip ...
"""

import sys
import re
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from parse_whatsapp import parse_messages, Message


# File extensions by type
AUDIO_EXTS = {'.m4a', '.opus', '.mp3', '.aac', '.ogg', '.wav'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.webm', '.3gp'}
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}

# Pattern to extract date from WhatsApp media filenames
# Example: 00000009-AUDIO-2024-05-12-13-12-04.m4a
FILENAME_PATTERN = re.compile(
    r'\d+-(?:AUDIO|VIDEO|PHOTO)-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})'
)


def get_file_type(filename: str) -> str | None:
    """Determine if file is audio, video, or photo."""
    ext = Path(filename).suffix.lower()
    if ext in AUDIO_EXTS:
        return 'audio'
    if ext in VIDEO_EXTS:
        return 'video'
    if ext in PHOTO_EXTS:
        return 'photos'
    return None


def parse_media_datetime(filename: str) -> datetime | None:
    """Extract datetime from WhatsApp media filename."""
    match = FILENAME_PATTERN.search(filename)
    if match:
        year, month, day, hour, minute, second = match.groups()
        return datetime(int(year), int(month), int(day), 
                       int(hour), int(minute), int(second))
    return None


def find_context(media_dt: datetime, messages: list[Message], 
                 teacher_name: str = "Vaishnavi") -> str | None:
    """
    Try to find context for a media file from nearby messages.
    Looks for teacher messages within 30 minutes before/after the file timestamp.
    """
    if not media_dt:
        return None
    
    window = timedelta(minutes=30)
    
    for msg in messages:
        try:
            msg_dt = msg.datetime
        except:
            continue
        
        # Check if message is within time window
        if abs(msg_dt - media_dt) > window:
            continue
        
        # Prefer teacher messages
        if not msg.is_from_teacher(teacher_name):
            continue
        
        body_lower = msg.body.lower()
        
        # Look for context clues
        if 'recording' in body_lower or 'practice' in body_lower:
            return 'Practice-Recording'
        if 'sargam' in body_lower:
            return 'Sargam-Practice'
        if 'bandish' in body_lower:
            return 'Bandish'
        if 'alaap' in body_lower:
            return 'Alaap'
        if 'concert' in body_lower or 'performance' in body_lower:
            return 'Performance'
        if 'class' in body_lower:
            return 'Class'
    
    return None


def generate_filename(original: str, media_dt: datetime | None, 
                      context: str | None, file_type: str, 
                      counter: dict) -> str:
    """Generate a readable filename."""
    ext = Path(original).suffix.lower()
    
    if media_dt:
        date_str = media_dt.strftime('%Y-%m-%d')
        time_str = media_dt.strftime('%H%M')
    else:
        date_str = 'unknown-date'
        time_str = '0000'
    
    # Build the new name
    if context:
        base = f"{date_str}_{context}_{time_str}"
    else:
        # Default based on file type
        type_label = {
            'audio': 'Audio',
            'video': 'Video', 
            'photos': 'Photo'
        }.get(file_type, 'File')
        base = f"{date_str}_{type_label}_{time_str}"
    
    # Handle duplicates
    key = f"{file_type}:{base}"
    if key in counter:
        counter[key] += 1
        base = f"{base}_{counter[key]}"
    else:
        counter[key] = 1
    
    return f"{base}{ext}"


def organize_media(zip_paths: list[Path], output_dir: Path, 
                   messages: list[Message]) -> dict:
    """
    Extract and organize media from zip files.
    Returns stats about what was extracted.
    """
    stats = {'audio': 0, 'video': 0, 'photos': 0, 'skipped': 0}
    counter: dict[str, int] = {}
    
    # Create output directories
    for subdir in ['audio', 'video', 'photos']:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    for zip_path in zip_paths:
        print(f"\nProcessing: {zip_path.name}")
        
        with zipfile.ZipFile(zip_path, 'r') as z:
            for filename in z.namelist():
                file_type = get_file_type(filename)
                if not file_type:
                    continue
                
                # Parse datetime from filename
                media_dt = parse_media_datetime(filename)
                
                # Try to find context from chat
                context = find_context(media_dt, messages)
                
                # Generate new filename
                new_name = generate_filename(
                    filename, media_dt, context, file_type, counter
                )
                
                # Extract to appropriate folder
                target_path = output_dir / file_type / new_name
                
                # Read from zip and write to target
                data = z.read(filename)
                target_path.write_bytes(data)
                
                stats[file_type] += 1
                
                # Show progress
                print(f"  {file_type}: {filename} -> {new_name}")
    
    return stats


def main():
    if len(sys.argv) < 2:
        print("Usage: python organize_media.py <file1.zip> <file2.zip> ...")
        print("\nExtracts and organizes media files into:")
        print("  media/audio/   - Practice recordings, class audio")
        print("  media/video/   - Class videos, performances")
        print("  media/photos/  - Pictures")
        sys.exit(1)
    
    zip_paths = [Path(p) for p in sys.argv[1:] if Path(p).exists()]
    
    if not zip_paths:
        print("No valid zip files found.")
        sys.exit(1)
    
    # Output directory
    output_dir = Path('media')
    
    print("=" * 60)
    print("ORGANIZING MEDIA FILES")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir.absolute()}")
    
    # First, parse all messages for context
    print("\nParsing chat messages for context...")
    all_messages: list[Message] = []
    for zp in zip_paths:
        try:
            msgs = parse_messages(zp)
            all_messages.extend(msgs)
            print(f"  {zp.name}: {len(msgs)} messages")
        except Exception as e:
            print(f"  {zp.name}: Error - {e}")
    
    # Sort messages by datetime for efficient searching
    all_messages.sort(key=lambda m: m.datetime)
    
    # Organize media
    print("\nExtracting and renaming media files...")
    stats = organize_media(zip_paths, output_dir, all_messages)
    
    print("\n" + "=" * 60)
    print("COMPLETE!")
    print("=" * 60)
    print(f"\nExtracted to: {output_dir.absolute()}")
    print(f"  Audio files:  {stats['audio']}")
    print(f"  Video files:  {stats['video']}")
    print(f"  Photo files:  {stats['photos']}")
    print(f"\nFolders created:")
    print(f"  media/audio/")
    print(f"  media/video/")
    print(f"  media/photos/")


if __name__ == "__main__":
    main()
