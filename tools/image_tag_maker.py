import argparse
from pathlib import Path
import time
import sys

_templae1 = "![PHOTO]({})"
_templae2 = "[![PHOTO]({})]({})"

def main():
    parser = argparse.ArgumentParser(
        description="md内で参照するイメージをリンク付きで作成する")
    parser.add_argument("image_dir", help="Path to image directory")
    parser.add_argument("original_image_dir", help="Path to image directory")
    # 過去何時間分の画像を取得するか
    parser.add_argument("--hours", type=int, default=4, help="Number of hours to get images for")
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    assert image_dir.exists(), f"{image_dir} does not exist"
    original_image_dir = Path(args.original_image_dir)
    assert original_image_dir.exists(), f"{original_image_dir} does not exist"
    hours = args.hours

    # jpg / png ファイルを取得 (サブディレクトリも含む)
    image_files = list(image_dir.glob("**/*.jpg")) + list(image_dir.glob("**/*.png"))
    original_image_files = list(original_image_dir.glob("**/*.jpg")) + list(original_image_dir.glob("**/*.png"))

    # 更新日時でフィルタ
    image_files = [f for f in image_files if f.stat().st_mtime > (time.time() - 3600 * hours)]
    original_image_files = [f for f in original_image_files if f.stat().st_mtime > (time.time() - 3600 * hours)]

    if len(image_files) == 0:
        print("No images found")
        return

    # imagesに対して拡張子が同じで、名前が親フォルダ名が一緒で、名前が似ているものをペアにする
    pairs = []
    for image in image_files:
        found = False
        for original_image in original_image_files:
            if image.suffix == original_image.suffix and image.parent.name == original_image.parent.name:
                if original_image.stem in image.stem:
                    # "IMG_1234_1.jpg" と "IMG_1234.jpg" はペアになる 
                    pairs.append((image, original_image))
                    found = True
                    continue
        if not found:
            pairs.append((image, None))
    
    for image, original_image in pairs:
        if original_image is None:
            print(_templae1.format("/" + image.as_posix()))
            continue
        print(_templae2.format("/" + image.as_posix(), "/" + original_image.as_posix()))
        print()
    

if __name__ == "__main__":
    # print(sys.argv)
    main()

