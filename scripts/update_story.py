import os
import sys
import re
from pathlib import Path
import subprocess
from collections import Counter

# --- Environment ---
WORD = os.environ.get("WORD", "").strip()
AUTHOR = os.environ.get("AUTHOR", "unknown")
REPO = os.environ.get("GITHUB_REPOSITORY", "unknown/unknown")

# --- Files ---
STORY_FILE = Path("current_story.md")
STATS_FILE = Path("story_stats.md")
README_FILE = Path("README.md")
STORIES_DIR = Path("stories")
MAX_WORDS = 500
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
story_text = " ".join(words)

# --- Update current story file ---
STORY_FILE.write_text(story_text)

# --- Generate story stats ---
word_count = len(words)
most_common = Counter(words).most_common(5)

stats_table = "| Metric | Value |\n| --- | --- |\n"
stats_table += f"| Word count | {word_count} |\n"
stats_table += "| Most common words | " + ", ".join(f"{w}({c})" for w, c in most_common) + " |\n"
stats_table += f"| Most recent contributor | {AUTHOR} |\n"

# --- Write stats file ---
STATS_FILE.write_text(stats_table)
print(f"Updated stats file:\n{stats_table}")

# --- Update README ---
if README_FILE.exists():
    readme_text = README_FILE.read_text()
    
    # Update story section
    story_section = f"{story_text} [___](https://github.com/{REPO}/issues/new?title=)"
    readme_text = re.sub(
        r"<!-- STORY-START -->.*<!-- STORY-END -->",
        f"<!-- STORY-START -->\n{story_section}\n<!-- STORY-END -->",
        readme_text,
        flags=re.DOTALL
    )
    
    # Update stats section
    readme_text = re.sub(
        r"<!-- STATS-START -->.*<!-- STATS-END -->",
        f"<!-- STATS-START -->\n{stats_table}\n<!-- STATS-END -->",
        readme_text,
        flags=re.DOTALL
    )
    
    README_FILE.write_text(readme_text)

# --- Archive story if needed ---
if word_count >= MAX_WORDS:
    archive_file = STORIES_DIR / f"story_{len(list(STORIES_DIR.glob('story_*.md')))+1}.md"
    archive_file.write_text(story_text)
    STORY_FILE.write_text("")  # reset current story
    print(f"Story archived to {archive_file}")

# --- Commit & Push only if changes exist ---
subprocess.run(["git", "config", "user.name", "github-actions[bot]"])
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])

# Stage only relevant files
subprocess.run(["git", "add", str(STORY_FILE), str(STATS_FILE), str(README_FILE)])

# Check if there are staged changes
status = subprocess.run(["git", "diff", "--cached", "--quiet"])
if status.returncode != 0:  # changes exist
    subprocess.run(["git", "commit", "-m", f"Add word: {WORD}"], stderr=subprocess.DEVNULL)
    subprocess.run(["git", "push"])
else:
    print("No changes to commit. Skipping push.")
