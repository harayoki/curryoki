import os
import json
import glob
import requests
from requests.auth import HTTPBasicAuth
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET
from typing import List, Dict


HATENA_ID = os.getenv("HATENA_ID")  
HATENA_BLOG_ID = "curryoki.hatenablog.jp"
HATENA_API_KEY = os.getenv("HATENA_API_KEY")
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL")
assert HATENA_ID, "Please set HATENA_ID environment variables"
assert HATENA_API_KEY, "Please set HATENA_API_KEY environment variables"
assert MEDIA_BASE_URL, "Please set IMAGE_BASE_URL environment variables"

HATENA_BLOG_URL = f"https://blog.hatena.ne.jp/{HATENA_ID}/{HATENA_BLOG_ID}/atom/entry"

print(f"HATENA_BLOG_URL: {HATENA_BLOG_URL}")


PUBLISHED_FILE = "metadata/published.json"
MISSING_FILE = "metadata/missing.json"
TIME_ZONE = ZoneInfo("Asia/Tokyo")

published: Dict[str, List[str]]
try:
    with open(PUBLISHED_FILE, "r") as f:
        published = json.load(f)
except FileNotFoundError:
    published = {}



def convert_media_paths(content):
    """Markdown の相対パスのメディア（画像・動画・ファイル）を GitHub BLOB URL に変換"""
    # 正規表現の修正版
    return re.sub(
        r"!\[(.*?)\]\((?!https?:\/\/)([^)\s]+?\.(jpg|jpeg|png|gif|webp|svg|zip|mp4|mp3|blend|psd|ai)(\?.*?)?)\)",
        lambda m: f"![{m.group(1)}]({MEDIA_BASE_URL}/{m.group(2)})",
        content
    )

def get_commit_time(file) -> datetime:
    commit_info = os.popen(f"git log -1 --pretty=format:%ci -- {file}").read().split(",")
    # git log -1 --pretty=format:"%ci" -- <ファイル名>
    # print(f"commit_info: {commit_info}")
    commit_time = datetime.fromtimestamp(int(commit_info[0]))
    if commit_time.tzinfo is None:
        commit_time = commit_time.replace(tzinfo=TIME_ZONE)
    return commit_time


# 記事の一覧を取得
md_files = glob.glob("articles/**/*.md", recursive=True)
# 更新が古いほうを先頭に並び替える
md_files.sort(key=lambda f: get_commit_time(f))


# metadata/published.json ファイルの更新時刻を得る
meta_data_commit_time = get_commit_time(PUBLISHED_FILE)
print(f"meta_data_commit_time: {meta_data_commit_time} {type(meta_data_commit_time)}")

# **新規 or 更新の処理**
for md_file in md_files:
    category = md_file.split("/")[1]  

    # 記事のポスト時刻を得る
    post_url, last_post_time_str = published.get(md_file, [None, ""])
    if last_post_time_str != "":
        last_post_time = datetime.fromisoformat(last_post_time_str)
    else:
        last_post_time = None
    print(f"last_post_time: {last_post_time} {type(last_post_time)}")
    if last_post_time is None:
        # print(f"New {md_file}")
        pass
    
    # コミットメタ情報を得る
    commit_time = get_commit_time(md_file)
    if commit_time.tzinfo is None:
        commit_time = commit_time.replace(tzinfo=TIME_ZONE)


    # 記事のコミット時刻が metadata　のコミット時刻より古い場合は無視する
    if meta_data_commit_time >=  commit_time:
        print(f"Skip {md_file}: {commit_time} <= meta:{meta_data_commit_time}")
        continue
    print(f"no skip {md_file}: {commit_time} > meta:{meta_data_commit_time}")

    continue
 
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()

    content = convert_media_paths(content)
    
    lines = content.split("\n")

    # 空白行をスキップし、最初の `# ` で始まる行を探す
    title_line = next((line for line in lines if line.strip() and line.startswith("# ")), None)

    # タイトルが見つかった場合のみ削除
    if title_line:
        title = title_line.strip("# ").strip()
        filtered_lines = [line for line in lines if line != title_line]
    else:
        title = os.path.basename(md_file)  # ファイル名をタイトルにする
        filtered_lines = lines  # 本文は変更しない

    # 投稿用の本文
    content_cleaned = "\n".join(filtered_lines)


    method = "PUT" if post_url else "POST"

    now = datetime.now(TIME_ZONE)
    # print(f"now_iso: {now} {type(now)}")
    last_post_time = last_post_time if last_post_time else now

    entry = Element("entry", xmlns="http://www.w3.org/2005/Atom")
    SubElement(entry, "title").text = title
    SubElement(entry, "content", {"type": "text/markdown"}).text = content_cleaned
    SubElement(entry, "category", term=category)
    SubElement(entry, "published").text = last_post_time.isoformat()
    SubElement(entry, "updated").text = now.isoformat()

    headers = {
        "Content-Type": "application/xml",
        # "X-WSSE": wsse(HATENA_ID, HATENA_API_KEY)
    }

    url = post_url if post_url else HATENA_BLOG_URL
    response = requests.request(
        method,
        url,
        auth=HTTPBasicAuth(HATENA_ID, HATENA_API_KEY),
        headers=headers,
        data=tostring(entry)
    )

    if response.status_code in [200, 201]:
        print(f"Published {md_file}: {title}")

        # 投稿 URL を取得（Location ヘッダ or XML）
        post_url = response.headers.get("Location")
        if not post_url:
            # 更新時は Location が戻ってこない模様
            try:
                root = ET.fromstring(response.content)
                post_url = root.find(".//{http://www.w3.org/2005/Atom}link[@rel='edit']").attrib["href"]
            except Exception:
                print(f"⚠️ {md_file}: 投稿URLを取得できませんでした。")
                continue  # published.json を更新せずスキップ 
        if post_url:
            now = datetime.now(TIME_ZONE)
            # print(f"post_url: {post_url}")
            published[md_file] = [post_url, now.isoformat()]

    else:
        print(f"Failed to publish {md_file}: {response.text}")

with open(PUBLISHED_FILE, "w") as f:
    json.dump(published, f, indent=2)


missing = {}
# published にあるがローカルに見つからないファイルを一覧にしておく
for f, url in published.items():
    if not os.path.exists(f):
        missing[f] = url

try:
    with open(MISSING_FILE, "w") as f:
        json.dump(missing, f, indent=2)
except Exception as e:
    print(f"Failed to write {MISSING_FILE}: {e}")
# この一覧にあるものはぶりぐ側で手作業で消したほうがいいかもしれない。



"""
MEMO

仕様：githubリポジトリはpublicであることを前提としている,privateの場合メディアのURLが正しく機能しない
仕様：ブログ側で記事を消すとpublished.json に記録が残るが対応していない、そのままサイトの記事にも残る
仕様：ローカルの記事ファイルを消した場合でもpublished.json に記録が残るが対応していない、そのままサイトの記事にも残る
仕様：違うカテゴリ内で別のカテゴリと同じ名前のmdファイルを置くと管理がおかしくなる
"""


# test用
# curl -u "curryoki:*****" https://blog.hatena.ne.jp/curryoki/curryoki.hatenablog.jp/atom/entry
