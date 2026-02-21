import os
import re
import json
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key from .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY not found in .env file.")
    print("Please create a .env file with: GOOGLE_API_KEY=your_key_here")
    exit(1)

genai.configure(api_key=api_key)

# Models to try in order (different quota pools)
MODELS = ["gemini-2.0-flash", "gemini-2.5-flash"]

# The taxonomy from requirements.md
TAXONOMY_PROMPT = """
Identify the following for this Hindustani classical music audio:
1. Raga: The melodic framework (e.g., Brindavani Sarang, Yaman, Bhairav, Bhupali, etc.)
   NOTE: Use "Bhupali" (not "Bhoopali") as the standard spelling.
2. Composition Type: Alaap (slow improv), Bandish (song with lyrics), or Taan (fast runs)
3. Paltaas: Is this a Sargam/Paltaa practice exercise? (Yes/No)
4. Taal: The rhythm cycle if audible (e.g., Teentaal - 16, Ektaal - 12, Jhaptaal - 10, Rupak - 7, Dadra - 6)

Return ONLY valid JSON with no extra text, in this exact format:
{
  "raga": "name or Unknown",
  "composition_type": "Alaap/Bandish/Taan/Unknown",
  "paltaas": true/false,
  "taal": "name or Unknown",
  "explanation": "Brief reason for classification"
}
"""

def _fix_json(text: str) -> str:
    """Try to fix common JSON issues from LLM output."""
    # Strip markdown code fences
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    # Fix unescaped quotes inside string values by finding the JSON object
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return text

def categorize_audio(file_path: Path):
    print(f"Processing: {file_path.name}...", flush=True)
    
    # Support common formats
    mime_type = "audio/mpeg"
    if file_path.suffix.lower() == ".wav":
        mime_type = "audio/wav"
    elif file_path.suffix.lower() == ".opus":
        mime_type = "audio/opus"
    elif file_path.suffix.lower() == ".ogg":
        mime_type = "audio/ogg"
    elif file_path.suffix.lower() == ".amr":
        mime_type = "audio/amr"

    retries = 5
    for attempt in range(retries):
        for model_name in MODELS:
            try:
                audio_file = genai.upload_file(path=str(file_path), mime_type=mime_type)
                
                # Wait for file to be processed
                while audio_file.state.name == "PROCESSING":
                    time.sleep(2)
                    audio_file = genai.get_file(audio_file.name)
                    
                if audio_file.state.name == "FAILED":
                    raise Exception("File processing failed.")

                model = genai.GenerativeModel(model_name)
                response = model.generate_content([audio_file, TAXONOMY_PROMPT])
                
                # Parse JSON from response
                text = _fix_json(response.text)
                result = json.loads(text)
                # Normalize Bhoopali -> Bhupali
                if result.get("raga", "").lower() in ("bhoopali", "bhoopali"):
                    result["raga"] = "Bhupali"
                print(f"  -> {result.get('raga', '?')} / {result.get('composition_type', '?')} [{model_name}]", flush=True)
                return result
            except Exception as e:
                err = str(e)
                if "429" in err:
                    print(f"  Quota hit on {model_name}, trying next model...", flush=True)
                    continue  # try next model
                if "JSON" in err or "Expecting" in err or "delimiter" in err:
                    print(f"  JSON parse error on {model_name}, retrying...", flush=True)
                    continue  # try next model
                print(f"  Error ({model_name}): {e}", flush=True)
                return None
        # All models quota-limited, back off before retrying
        wait_time = 60 * (attempt + 1)
        print(f"  All models quota-limited, waiting {wait_time}s... (attempt {attempt+1}/{retries})", flush=True)
        time.sleep(wait_time)

    print(f"  Skipped after {retries} retries.", flush=True)
    return None

def main():
    audio_dir = Path("media/audio")
    output_file = Path("data/audio_categories.json")
    
    if not audio_dir.exists():
        print(f"Error: {audio_dir} does not exist.")
        return

    # Load existing categories to avoid re-processing
    categories = {}
    if output_file.exists():
        with open(output_file, "r") as f:
            categories = json.load(f)

    audio_files = list(audio_dir.glob("*.*"))
    # Filter for audio extensions
    audio_files = [f for f in audio_files if f.suffix.lower() in [".m4a", ".mp3", ".wav", ".opus", ".ogg", ".amr"]]
    
    remaining = [f for f in audio_files if f.name not in categories]
    
    print(f"Found {len(audio_files)} audio files.", flush=True)
    print(f"Already categorized: {len(categories)}", flush=True)
    print(f"Remaining: {len(remaining)}", flush=True)
    print(f"Wait between files: 60s (to stay within free tier quota)", flush=True)
    print(f"Estimated time: ~{len(remaining)} minutes\n", flush=True)
    
    newly_processed = 0
    for i, file_path in enumerate(remaining):
        print(f"[{i+1}/{len(remaining)}] ", end="", flush=True)
        
        result = categorize_audio(file_path)
        if result:
            categories[file_path.name] = result
            newly_processed += 1
            
            # Save progress after every file
            with open(output_file, "w") as f:
                json.dump(categories, f, indent=2)
        
        # Wait 60s between files to stay within free tier (15 RPM)
        if i < len(remaining) - 1:
            print(f"  Waiting 60s before next file...", flush=True)
            time.sleep(60)

    print(f"\nFinished. Processed {newly_processed} new files.", flush=True)
    print(f"Total categorized: {len(categories)} / {len(audio_files)}", flush=True)
    print(f"Results saved to {output_file}", flush=True)

if __name__ == "__main__":
    main()
