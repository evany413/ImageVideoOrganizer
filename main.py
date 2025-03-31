from pathlib import Path
import shutil
import ffmpeg
from PIL import Image
import os

VIDEO_EXTENSIONS = ["mp4", "avi", "mov", "wmv", "flv", "mpeg", "mpg", "m4v", "webm", "mkv"]
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "ico", "webp"]

def get_all_videos(input_dir: Path) -> list:
    videos = []
    for extension in VIDEO_EXTENSIONS:
        for video in input_dir.rglob(f"*.{extension}"):
            videos.append(video)
    return videos


def get_all_images(input_dir: Path) -> list:
    images = []
    for extension in IMAGE_EXTENSIONS:
        for image in input_dir.rglob(f"*.{extension}"):
            images.append(image)
    return images

def convert_videos(videos: list, input_dir: Path, output_dir: Path):
    for video in videos:
        print(video)
        # Get relative path from input_dir to preserve structure
        rel_path = video.relative_to(input_dir)
        # Create output path maintaining the same structure
        output_path = output_dir / rel_path.parent / f"{video.stem}.mp4"
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        ffmpeg.input(str(video)).output(str(output_path), 
            vcodec='libx264',
            acodec='aac',     
            crf=21,          # Constant Rate Factor (CQ) - lower means better quality
            audio_bitrate='128k',
            movflags='+faststart',  # Web optimized for streaming
            vf='scale=-1:720:force_original_aspect_ratio=decrease'  # Scale down to 720p if larger
        ).run() 


def convert_images(images: list, input_dir: Path, output_dir: Path):
    print(images)
    for image in images:
        print(image)
        try:
            # Get relative path from input_dir to preserve structure
            rel_path = image.relative_to(input_dir)
            # Create output path maintaining the same structure
            output_path = output_dir / rel_path.parent / f"{image.stem}.jpg"
            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with Image.open(image).convert("RGB") as img:
                img.save(output_path, 
                    'JPEG',
                    quality=85,
                    optimize=True,
                    progressive=True
                )
        except Exception as e:
            print(f"Error converting {image}: {str(e)}")


INPUT_DIR = "_original"
OUTPUT_DIR = "_converted"

def main():
    input_dir = Path(INPUT_DIR)
    output_dir = Path(OUTPUT_DIR)
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)

    videos = get_all_videos(input_dir)
    images = get_all_images(input_dir)

    convert_videos(videos, input_dir, output_dir)
    convert_images(images, input_dir, output_dir)


if __name__ == "__main__":
    main()