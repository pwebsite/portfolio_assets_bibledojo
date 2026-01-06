import os
import re
import urllib.request
import urllib.parse
import sys
import glob

# --- CONFIGURATION ---
LIVE_URL = "https://www.pollylal.com/design/bibledojo-by-basil-tech-gamified-learning-experience"
OUTPUT_FILENAME = "BibleDojo_FINAL_LIVE.md"

# GitHub Settings
GITHUB_USER = "pwebsite"
REPO_NAME = "portfolio_images"
BRANCH = "main"
SUBFOLDER = "bibledojo"
# ---------------------

def get_cdn_link(filename):
    return f"https://cdn.jsdelivr.net/gh/{GITHUB_USER}/{REPO_NAME}@{BRANCH}/{SUBFOLDER}/{filename}"

def fetch_live_html():
    print(f"🌍 Connecting to {LIVE_URL}...")
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    req = urllib.request.Request(LIVE_URL, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"❌ Error fetching site: {e}")
        sys.exit(1)

def main():
    # 1. FIND THE MARKDOWN FILE
    md_files = glob.glob("*.md")
    # Filter out previous output files to avoid confusion
    md_files = [f for f in md_files if "FINAL" not in f and "Paste_Ready" not in f]
    
    if not md_files:
        print("❌ Error: No Markdown (.md) file found.")
        print("   -> Drag your Notion export file into this folder.")
        return
    
    md_baseline = md_files[0]
    print(f"📄 Using Text Baseline: {md_baseline}")

    # 2. SCRAPE LIVE MEDIA IN ORDER
    html_content = fetch_live_html()
    
    print("🔍 Scanning live site for media order...")
    
    # We split by tags to iterate linearly
    tokens = re.split(r'(<img[^>]+>|<iframe[^>]+>)', html_content)
    
    master_media = []
    img_count = 0
    seen_urls = set() # To avoid duplicates if Framer uses srcset/lazy-loading twice

    print("⬇️  Downloading images from live site...")

    for token in tokens:
        # A. IMAGES (Focus on framerusercontent to avoid icons/junk)
        if token.startswith("<img") and "src=" in token:
            # Check if it's a real content image
            if "framerusercontent" in token:
                src_match = re.search(r'src="([^"]+)"', token)
                if src_match:
                    url = src_match.group(1)
                    
                    # Clean URL (remove query params like ?w=...)
                    clean_url = url.split('?')[0]
                    
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        img_count += 1
                        
                        # Name sequentially
                        ext = os.path.splitext(clean_url)[1]
                        if not ext: ext = ".png" # default fallback
                        new_filename = f"bibledojo_{img_count:02d}{ext}"
                        
                        # Download
                        try:
                            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req) as r:
                                with open(new_filename, 'wb') as f: f.write(r.read())
                        except:
                            print(f"   ⚠️ Failed to download: {url}")

                        master_media.append({'type': 'image', 'filename': new_filename})

        # B. VIDEOS (Vimeo/YouTube Iframes)
        elif token.startswith("<iframe"):
            if "vimeo" in token or "youtube" in token:
                src_match = re.search(r'src="([^"]+)"', token)
                if src_match:
                    raw_url = src_match.group(1)
                    # Normalize Vimeo links
                    if "player.vimeo.com" in raw_url:
                        # Extract ID
                        vid_id = re.search(r'video/(\d+)', raw_url)
                        if vid_id:
                            clean_vimeo = f"https://vimeo.com/{vid_id.group(1)}"
                            master_media.append({'type': 'video', 'url': clean_vimeo})
                    # Normalize YouTube links
                    elif "youtube.com/embed" in raw_url:
                        vid_id = re.search(r'embed/([a-zA-Z0-9_-]+)', raw_url)
                        if vid_id:
                            clean_yt = f"https://www.youtube.com/watch?v={vid_id.group(1)}"
                            master_media.append({'type': 'video', 'url': clean_yt})

    print(f"✅ Scraped Sequence: {img_count} Images, {len([x for x in master_media if x['type']=='video'])} Videos.")


    # 3. MERGE INTO MARKDOWN
    print("💉 Injecting media into Markdown...")
    
    with open(md_baseline, 'r', encoding='utf-8') as f:
        md_lines = f.readlines()

    final_lines = []
    cursor = 0

    for line in md_lines:
        # Check for ANY image placeholder ![...](...)
        if re.search(r'!\[.*?\]\(.*?\)', line):
            
            # We found a slot in the text. Fill it with the next item from the site.
            if cursor < len(master_media):
                item = master_media[cursor]
                
                if item['type'] == 'video':
                    # It's a video!
                    # If Notion exported an image placeholder here, it was likely a "video poster".
                    # We replace the entire image line with the Video Link.
                    final_lines.append(f"\n{item['url']}\n")
                    print(f"   + Swapped placeholder for Video: {item['url']}")
                    cursor += 1
                
                elif item['type'] == 'image':
                    # It's an image!
                    new_link = get_cdn_link(item['filename'])
                    final_lines.append(f"![Image]({new_link})\n")
                    cursor += 1
            else:
                # No more live media found? Keep original or leave blank.
                # Usually better to comment it out so no broken icons appear.
                final_lines.append(f"\n")
        else:
            final_lines.append(line)

    with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    print(f"\n🎉 DONE! Created: {OUTPUT_FILENAME}")
    print("👉 Push the images to GitHub, then copy the text from the new file.")

if __name__ == "__main__":
    main()