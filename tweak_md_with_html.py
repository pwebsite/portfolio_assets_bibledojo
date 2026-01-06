import os
import re
import glob
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
INPUT_HTML = "fixed_page.html"
OUTPUT_FILENAME = "BibleDojo_FINAL_FIXED.md"

GITHUB_USER = "pwebsite"
REPO_NAME = "portfolio_images"
BRANCH = "main"
SUBFOLDER = "bibledojo"

# Toggle this based on which project you are currently processing
USE_JSDELIVR = True

def get_link(filename):
    if USE_JSDELIVR:
        # High performance, but requires repo < 50MB
        return f"https://cdn.jsdelivr.net/gh/{GITHUB_USER}/{REPO_NAME}@{BRANCH}/{SUBFOLDER}/{filename}"
    else:
        # No 50MB limit, but slower and subject to rate limits
        return f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/{BRANCH}/{SUBFOLDER}/{filename}"

def main():
    md_files = glob.glob("*.md")
    md_baseline = [f for f in md_files if "FINAL" not in f and "FIXED" not in f][0]

    with open(INPUT_HTML, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    master_media = [os.path.basename(img.get("src", "")).split('?')[0] for img in soup.find_all("img")]

    with open(md_baseline, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    final_lines = []
    cursor = 0
    for line in lines:
        if re.search(r'!\[.*?\]\(.*?\)', line):
            if cursor < len(master_media):
                final_lines.append(f"![Image]({get_link(master_media[cursor])})\n")
                cursor += 1
            else:
                final_lines.append("\n")
        else:
            final_lines.append(line)

    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    print(f"✅ Created {OUTPUT_FILENAME} using {'jsDelivr' if USE_JSDELIVR else 'GitHub Raw'}")

if __name__ == "__main__":
    main()