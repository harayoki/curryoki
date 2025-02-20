from PIL import Image, ImageDraw
from typing import Tuple, List
from pathlib import Path
import argparse



def add_stripe_margin(img, margin_size, color1, color2, stripe_width=10):
    """
    指定された2色の斜めストライプマージンを追加する。
    :param img: PIL Image オブジェクト
    :param margin_size: 余白のサイズ（px）
    :param color1: ストライプの色1
    :param color2: ストライプの色2
    :param stripe_width: ストライプの幅
    :return: マージン付きのPIL Image オブジェクト
    """
    new_size = (img.width + 2 * margin_size, img.height + 2 * margin_size)
    outer_img = Image.new("RGB", new_size, color2)
    draw = ImageDraw.Draw(outer_img)
    
    # 斜めストライプを全面に描画
    for i in range(-new_size[0] - new_size[1], new_size[0] + new_size[1], stripe_width * 2):
        draw.polygon([
            (i, 0), 
            (i + stripe_width, 0), 
            (i + stripe_width + new_size[1], new_size[1]), 
            (i + new_size[1], new_size[1])
        ], fill=color1)
    
    # 画像を中央に貼り付け
    outer_img.paste(img, (margin_size, margin_size))
    
    return outer_img


def add_single_color_margin(img, margin_top, margin_right, margin_bottom, margin_left, color):
    """
    指定された単色のマージンを追加する。
    :param img: PIL Image オブジェクト
    :param margin_top: 上部の余白のサイズ（px）
    :param margin_right: 右部の余白のサイズ（px）
    :param margin_bottom: 下部の余白のサイズ（px）
    :param margin_left: 左部の余白のサイズ（px）
    :param color: マージンの色
    :return: マージン付きのPIL Image オブジェクト
    """
    new_size = (img.width + margin_left + margin_right, img.height + margin_top + margin_bottom)
    new_img = Image.new("RGB", new_size, color)
    new_img.paste(img, (margin_left, margin_top))
    
    return new_img



def adjust_image_size(image_path: str, width: int, height: int) -> Image.Image | None:
    try:
        image = Image.open(image_path)
    except Exception as e:
        print(f"Failed to open the image: {image_path}")
        return None
    assert width >= 0 or height >= 0
    if width < 0:
        width = image.width * height // image.height
    if height < 0:
        height = image.height * width // image.width
    image_ratio = image.width / image.height
    resize_ratio = width / height
    # crop the image to the center
    if image_ratio != resize_ratio:
        if image_ratio > resize_ratio:
            crop_width = image.height * resize_ratio
            crop_left = (image.width - crop_width) // 2
            crop_right = crop_left + crop_width
            image = image.crop((crop_left, 0, crop_right, image.height))
        else:
            crop_height = image.width / resize_ratio
            crop_top = (image.height - crop_height) // 2
            crop_bottom = crop_top + crop_height
            image = image.crop((0, crop_top, image.width, crop_bottom))
    resized_image = image.resize((width, height))
    return resized_image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=str, help="Path to the image file or directory")
    parser.add_argument("-ww", "--width", type=int, default=-1, help="Width of the image")
    parser.add_argument("-hh", "--height", type=int, default=-1, help="Height of the image")
    parser.add_argument("-stripe", "--stripe_margin", type=int, default=20,
                        help="Width of the stripe margin, total width and height will be 2 * stripe_margin + original size")
    parser.add_argument("-margin", "--margin_width", type=int, default=60,
                        help="Width of the margin, total width and height will be 2 * margin_width + original size")
    parser.add_argument("-tmw", "--top_mergin_width", type=int, default=-1,
                         help="Width of the top margin if different from the margin width")
    parser.add_argument("-bmw", "--bottom_mergin_width", type=int, default=-1,
                         help="Width of the bottom margin if different from the margin width")
    parser.add_argument("-mc", "--margin_color", type=str, default="FFFFFF", help="Color of the margin")
    parser.add_argument("--output", type=str, default="", help="Output directory")
    parser.add_argument("--allow_overwrite", action="store_true", help="Allow overwriting the existing files")

    args = parser.parse_args()
    if args.width < 0 and args.height < 0:
        raise ValueError("Either width or height must be specified")

    input_path = Path(args.image_path)
    image_paths: List[Path]
    if input_path.is_dir():
        image_paths = list(input_path.glob("*"))
    else:
        image_paths = [input_path]
    image_paths = [path for path in image_paths if path.is_file() and not path.name.startswith(".")]
    image_paths = [path for path in image_paths if path.suffix.lower() in [".jpg", ".jpeg", ".png", ".gif"]]
    if len(image_paths) == 0:
        print("No image files found")
        return

    if args.output == "":
        output_dir = input_path
        if not output_dir.is_dir():
            output_dir = output_dir.parent
    else:
        output_dir = Path(args.output)
    if output_dir.is_file():
        raise ValueError("Output path must be a directory")
    if not output_dir.exists():
        output_dir.mkdir(parents=True)

    width = args.width
    height = args.height
    stripe_margin = args.stripe_margin
    margin_width = args.margin_width
    margin_color_rgb = tuple(int(args.margin_color[i:i + 2], 16) for i in (0, 2, 4))
    ouutput_parh: Path
    for image_path in image_paths:
        image = adjust_image_size(image_path, args.width, args.height)
        if image is None:
            continue
        if stripe_margin > 0:
            image = add_stripe_margin(image, stripe_margin, (0, 0, 0), (255, 255, 255))
        if margin_width > 0:
            margin_top = margin_width
            margin_right = margin_width
            margin_bottom = margin_width
            margin_left = margin_width
            if args.top_mergin_width >= 0:
                margin_top = args.top_mergin_width
            if args.bottom_mergin_width >= 0:
                margin_bottom = args.bottom_mergin_width
            image = add_single_color_margin(
                image, margin_top, margin_right, margin_bottom, margin_left, margin_color_rgb)

        output_path = output_dir / image_path.name
        if output_path.exists() and not args.allow_overwrite:
            # add index to the file name
            index = 1
            while True:
                output_path = output_dir / f"{image_path.stem}_{index}{image_path.suffix}"
                if not output_path.exists():
                    break
                index += 1
        image.save(output_path)        
        print(f"Resized: {image_path} -> {output_path} ({image.width}x{image.height})")


if __name__ == '__main__':
    main()

