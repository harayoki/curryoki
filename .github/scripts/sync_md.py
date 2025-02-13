import os
import json
import glob
import requests
from requests.auth import HTTPBasicAuth
import re
from datetime import datetime, timezone
from xml.etree.ElementTree import Element, SubElement, tostring
import random
import hashlib
import base64


def wsse(username, api_key):
    created = datetime.now().isoformat() + "Z"
    b_nonce = hashlib.sha1(str(random.random()).encode()).digest()
    b_digest = hashlib.sha1(b_nonce + created.encode() + api_key.encode()).digest()
    c = 'UsernameToken Username="{0}", PasswordDigest="{1}", Nonce="{2}", Created="{3}"'
    return c.format(username, base64.b64encode(b_digest).decode(), base64.b64encode(b_nonce).decode(), created)


# はてなブログのAPI設定
HATENA_ID = os.getenv("HATENA_ID")  
HATENA_BLOG_ID = "curryoki.hatenablog.jp"
HATENA_API_KEY = os.getenv("HATENA_API_KEY")
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL")

HATENA_BLOG_URL = f"https://blog.hatena.ne.jp/{HATENA_ID}/{HATENA_BLOG_ID}/atom/entry"

print(f"HATENA_BLOG_URL: {HATENA_BLOG_URL}")


PUBLISHED_FILE = "metadata/published.json"
try:
    with open(PUBLISHED_FILE, "r") as f:
        published = json.load(f)
except FileNotFoundError:
    published = {}

# 記事の一覧を取得
md_files = glob.glob("articles/**/*.md", recursive=True)
draft_files = glob.glob("_drafts/**/*.md", recursive=True)

def convert_image_paths(content):
    """相対パスをGitHub PagesのURLに変換"""
    return re.sub(r"!\[(.*?)\]\((.*?)\)", lambda m: f"![{m.group(1)}]({GITHUB_PAGES_URL}/{m.group(2)})", content)

# **新規 or 更新の処理**
for md_file in md_files:
    category = md_file.split("/")[1]  
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    content = convert_image_paths(content)
    
    lines = content.split("\n")
    title = next((line.strip("# ") for line in lines if line.startswith("# ")), os.path.basename(md_file))

    post_url = published.get(md_file, None)
    method = "PUT" if post_url else "POST"

    now_iso = datetime.now(timezone.utc).isoformat()

    published_time = published.get(md_file, now_iso)

    entry = Element("entry", xmlns="http://www.w3.org/2005/Atom")
    SubElement(entry, "title").text = title
    SubElement(entry, "content", {"type": "text/markdown"}).text = content
    SubElement(entry, "category", term=category)
    SubElement(entry, "published").text = published_time
    SubElement(entry, "updated").text = now_iso

    headers = {
        "Content-Type": "application/xml",
        "X-WSSE": wsse(HATENA_ID, HATENA_API_KEY)}

    url = post_url if post_url else HATENA_BLOG_URL

    r = requests.post(url, auth=(HATENA_ID, HATENA_API_KEY), data="")
   

    response = requests.request(
        method,
        url,
        # auth=HTTPBasicAuth(HATENA_ID, HATENA_API_KEY),
        headers=headers,
        data=tostring(entry)
    )

    if response.status_code in [200, 201]:
        print(f"Published {md_file} -> {title}")
        published[md_file] = response.headers.get("Location", "unknown")
        with open(PUBLISHED_FILE, "w") as f:
            json.dump(published, f, indent=2)
    else:
        print(f"Failed to publish {md_file}: {response.text}")

# **公開済み記事を「下書き」に戻す**
for draft_file in draft_files:
    if draft_file in published:
        print(f"Marking {draft_file} as draft")
        post_url = published[draft_file]

        # **下書きとして非公開にするため、URLを変更**
        draft_entry = Element("entry", xmlns="http://www.w3.org/2005/Atom")
        SubElement(draft_entry, "title").text = f"[DRAFT] {title}"
        SubElement(draft_entry, "updated").text = now_iso
        draft_headers = {"Content-Type": "application/xml"}

        # **公開URLを「/draft/」に変更**
        response = requests.put(
            post_url.replace("/entry/", "/draft/"),
            auth=(HATENA_ID, HATENA_API_KEY),
            headers=draft_headers,
            data=tostring(draft_entry)
        )

        if response.status_code == 200:
            print(f"Marked {draft_file} as draft")
        else:
            print(f"Failed to mark as draft: {response.text}")



# curl -u "curryoki:*****" https://blog.hatena.ne.jp/curryoki/curryoki.hatenablog.jp/atom/entry
