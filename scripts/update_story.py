import os, re, shutil
from collections import Counter
import nltk
from github import Github

nltk.download('averaged_perceptron_tagger')

# --- Environment ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
WORD = os.getenv("WORD").strip()
AUTHOR = os.getenv("AUTHOR")

STORY_FILE = "current_story.md"
STATS_FILE = "story_stats.md"
STORIES_DIR = "stories/"

# --- Validation ---
def validate_word(word, last_word=None):
    if not re.match(r'^[A-Za-z]+$', word):
        return False, "Word must be letters only"
    if ' ' in word:
        return False, "Word must be a single word"
    if last_word:
        last_pos = nltk.pos_tag([last_word])[0][1]
        new_pos = nltk.pos_tag([word])[0][1]
        if last_pos == new_pos and last_pos.startswith('JJ'):
            return False, "No repeated adjectives consecutively"
    return True, ""

# --- Load current story ---
story_text = ""
if os.path.exists(STORY_FILE):
    with open(STORY_FILE, "r") as f:
        story_text = f.read().strip()

last_word = story_text.split()[-1] if story_text else None

valid, msg = validate_word(WORD, last_word)
if not valid:
    print(f"Invalid word: {msg}")
    # Optionally comment on the issue using GitHub API
    exit(1)

# --- Append word ---
story_text += (" " if story_text else "") + WORD
with open(STORY_FILE, "w") as f:
    f.write(story_text)

# --- Update stats ---
words = story_text.split()
word_count = len(words)
common_words = Counter(words).most_common(10)
stats_md = f"Word count: {word_count}\nMost common words: {', '.join([w[0]+'('+str(w[1])+')' for w in common_words])}\nMost recent contributor: @{AUTHOR}"
with open(STATS_FILE, "w") as f:
    f.write(stats_md)

# --- Update README ---
recent_words = " ".join(words[-5:])
readme_text = f"# Collaborative Story\n\n**Current Story:**\n{recent_words} [___](https://github.com/YOUR_USERNAME/YOUR_REPO/issues/new?title=)\n\n**Stats:**\n{stats_md}"
with open("README.md", "w") as f:
    f.write(readme_text)

# --- Archive if 500 words ---
if word_count >= 500:
    os.makedirs(STORIES_DIR, exist_ok=True)
    story_num = len(os.listdir(STORIES_DIR)) + 1
    shutil.move(STORY_FILE, f"{STORIES_DIR}/story_{story_num}.md")
    shutil.move(STATS_FILE, f"{STORIES_DIR}/story_{story_num}_stats.md")
    # Reset new story
    starter = "Once"
    with open(STORY_FILE, "w") as f:
        f.write(starter)
    with open(STATS_FILE, "w") as f:
        f.write(f"Word count: 1\nMost common words: {starter}(1)\nMost recent contributor: system")
