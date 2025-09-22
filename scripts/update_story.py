import os
import sys
import re
from pathlib import Path
import subprocess

# Get environment variables
WORD = os.environ.get("WORD", "").strip()
AUTHOR = os.environ.get("AUTHOR", "unknown")

# File paths
STORY_FILE = Path("current_story.md")
STATS_FILE = Path("story_stats.md")
README_FILE = Path("README.md")
STORIES_DIR = Path("stories")
MAX_WORDS = 500

# Ensure stories directory exists
STORIES_DIR.mkdir(exist_ok=True)

# --- Validation ---
def validate_word(word):
    if not word:
        return False, "Word is empty"
    if len(word.split()) > 1:
        return False, "Only single words allowed"
    if not re.match(r"^[a-zA-Z'-]+$", word):
        return False, "Word contains invalid characters"
    return True, "Valid"

valid, msg = validate_word(WORD)
if not valid:
    print(f"Rejected word '{WORD}': {msg}")
    sys.exit(0)

# --- Load current story ---
if STORY_FILE.exists():
    story_text = STORY_FILE.read_text().strip()
else:
    story_text = ""

words = story_text.split()
words.append(WORD)

# --- Update story ---
STORY_FILE.write_text(" ".join(words))

# --- Update stats ---
from collections import Counter

word_count = len(words)
most_common = Counter(words).most_common(5)
most_common_str = ", ".join(f"{w}({c})" for w, c in most_common)
stats_text = f"""Word count: {word_count}
Most common words: {most_common_str}
Most recent contributor: {AUTHOR}
"""
STATS_FILE.write_text(stats_text)

# --- Update README (replace first link with last word issue link) ---
if README_FILE.exists():
    readme_text = README_FILE.read_text()
    new_story_text = story_text.replace("\n", " ") + " [___](https://github.com/VectorSophie/Storytime/issues/new?title=)"
    updated_readme = re.sub(
        r"<!-- STORY-START -->.*<!-- STORY-END -->",
        f"<!-- STORY-START -->\n{new_story_text}\n<!-- STORY-END -->",
        readme_text,
        flags=re.DOTALL
    )
    README_FILE.write_text(updated_readme)

# --- Archive if needed ---
if word_count >= MAX_WORDS:
    archive_file = STORIES_DIR / f"story_{len(list(STORIES_DIR.glob('story_*.md')))+1}.md"
    archive_file.write_text(" ".join(words))
    STORY_FILE.write_text("")  # reset story

# --- Commit & Push ---
subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"Add word: {WORD}"])
subprocess.run(["git", "push"])
