from PIL import Image
from typing import Tuple, List
from pathlib import Path
import argparse


def adjust_image_size(image_path: str, width: int, height: int) -> Image.Image:
    image = Image.open(image_path)
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
    ouutput_parh: Path
    for image_path in image_paths:
        image = adjust_image_size(image_path, args.width, args.height)
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
        print(f"Resized: {image_path}")


if __name__ == '__main__':
    main()

