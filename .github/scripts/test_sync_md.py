import sys
import os
import re

os.environ["HATENA_ID"] = "DUMMY_HATENA_ID"
os.environ["HATENA_API_KEY"] = "DUMMY_HATENA_API_KEY"
os.environ["MEDIA_BASE_URL"] = "https://raw.githubusercontent.com/harayoki/curryoki/refs/heads/main"
HATENA_ID = os.environ["HATENA_ID"]
HATENA_API_KEY = os.environ["HATENA_API_KEY"]
MEDIA_BASE_URL = os.environ["MEDIA_BASE_URL"]

# sys.path.append(".")
# from sync_md import convert_media_paths


def convert_media_paths(content):
    # img タグの相対パスを GitHub BLOB URL に変換
    content = re.sub(
        r"<img src=\"(?!https?:\/\/)([^>\s]+?\.(jpg|jpeg|png|gif|webp|svg))\"",
        lambda m: f"<img src=\"{MEDIA_BASE_URL}/{m.group(1)}\"",
        content
    )
    """Markdown の相対パスのメディア（画像・動画・ファイル）を GitHub BLOB URL に変換"""
    content = re.sub(
        r"\((?!https?:\/\/)([^)\s]+?\.(jpg|jpeg|png|gif|webp|svg|zip|mp4|mp3|blend|psd|ai)(\?.*?)?)\)",
        lambda m: f"({MEDIA_BASE_URL}/{m.group(1)})",
        content
    )
    # (http https ...):// 以外の 二重スラッシュを除去
    content = content.replace("://", "___COLONSLASHSLASH___")
    content = content.replace("//", "/")
    content = content.replace("___COLONSLASHSLASH___", "://")
    return content


contents = [
    "![alt](/images/image.png)",
    "[text](/images/image2.png)",
    "[![alt](/images/image.png)](/images/image2.png)"
]

expecteds = [
    f"![alt]({MEDIA_BASE_URL}/images/image.png)",
    f"[text]({MEDIA_BASE_URL}/images/image2.png)",
    f"[![alt]({MEDIA_BASE_URL}/images/image.png)]({MEDIA_BASE_URL}/images/image2.png)"
]

def test_convert_media_paths():
    has_error = False
    for content, expected in zip(contents, expecteds):
        cnoverted = convert_media_paths(content)    
        if cnoverted != expected:
            print(f"coverted: {cnoverted}")
            print(f"expected: {expected}")
            has_error = True
        else:
            print(f"OK: {cnoverted}")
    assert not has_error

if __name__ == "__main__":
    test_convert_media_paths()
