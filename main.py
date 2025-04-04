from pathlib import Path
import shutil
import ffmpeg
from PIL import Image
from opencc import OpenCC
import subprocess
from collections import deque

cc = OpenCC('s2tw')

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

def get_best_available_encoder():
    """Detect the best available hardware encoder, fall back to CPU if none available."""
    try:
        # Check available encoders using ffmpeg -encoders
        result = subprocess.run(['ffmpeg', '-encoders'], capture_output=True, text=True)
        encoders = result.stdout  # FFmpeg outputs encoder list to stdout
        print("Available encoders:", encoders)
        
        # Check for NVIDIA GPU encoder
        if 'h264_nvenc' in encoders:
            print("Found NVIDIA GPU encoder")
            return 'h264_nvenc'
        # Check for Intel QuickSync encoder
        elif 'h264_qsv' in encoders:
            print("Found Intel QuickSync encoder")
            return 'h264_qsv'
        # Check for AMD AMF encoder
        elif 'h264_amf' in encoders:
            print("Found AMD AMF encoder")
            return 'h264_amf'
        else:
            print("No hardware encoders found, using CPU encoder")
            return 'libx264'
    except Exception as e:
        print(f"Error detecting encoders: {str(e)}")
        return 'libx264'

def convert_videos(videos: list, input_dir: Path, output_dir: Path):
    # Get the best available encoder once for all conversions
    encoder = get_best_available_encoder()
    print(f"Using encoder: {encoder}")
    
    for video in videos:
        print(video)
        # Get relative path from input_dir to preserve structure
        rel_path = video.relative_to(input_dir)
        # Create output path maintaining the same structure
        output_path = output_dir / rel_path.parent / f"{video.name}.mp4"
        # Create parent directories if they don't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Base output parameters
            output_params = {
                'vcodec': encoder,
                'acodec': 'aac',
                'audio_bitrate': '128k',
                'movflags': '+faststart',
                'vf': 'scale=trunc(iw/2)*2:trunc(ih/2)*2:force_original_aspect_ratio=decrease'
            }
            
            # Add encoder-specific parameters
            if encoder == 'libx264':
                output_params['crf'] = 21
            elif encoder == 'h264_nvenc':
                output_params['rc'] = 'vbr'
                output_params['cq'] = 21
            elif encoder == 'h264_qsv':
                output_params['global_quality'] = 21
            elif encoder == 'h264_amf':
                output_params['quality'] = 'quality'
                output_params['qp'] = 21
            
            ffmpeg.input(str(video)).output(str(output_path), **output_params).run()
        except Exception as e:
            print(f"Error converting {video}: {str(e)}")


def convert_images(images: list, input_dir: Path, output_dir: Path):
    for image in images:
        print(image)
        try:
            # Get relative path from input_dir to preserve structure
            rel_path = image.relative_to(input_dir)
            # Create output path maintaining the same structure
            output_path = output_dir / rel_path.parent / f"{image.name}.jpg"
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

def organize_files(output_dir: Path):
    
    idx = 0
    # First remove any files that aren't mp4 or jpg
    for file in output_dir.rglob("*"):
        if file.is_file():
            if file.suffix.lower() not in ['.mp4', '.jpg']:
                file.unlink()
            else:
                file.rename(file.parent / f"{file.stem}_temp{idx}{file.suffix}")
                idx += 1

    clear_empty_folders(output_dir)

    # Process directories level by level
    current_level = [output_dir]
    while current_level:
        next_level = []
        
        # Process each directory in current level
        for current_dir in current_level:
            # Skip if this is a V or P folder
            if current_dir.name in ['V', 'P']:
                continue
                
            # Check if current directory has V or P folders
            has_v_folder = (current_dir / 'V').exists()
            has_p_folder = (current_dir / 'P').exists()
            
            # If no V or P folders, create them and move files
            if not has_v_folder and not has_p_folder:
                # Collect files in current directory
                files_to_move = []
                for file in current_dir.iterdir():
                    if file.is_file() and file.suffix.lower() in ['.mp4', '.jpg']:
                        files_to_move.append(file)
                
                # Create V and P folders if we have files to move
                if files_to_move:
                    v_folder = current_dir / "V"
                    p_folder = current_dir / "P"
                    v_folder.mkdir(exist_ok=True)
                    p_folder.mkdir(exist_ok=True)
                    
                    # Move files to appropriate folders
                    for idx, file in enumerate(files_to_move, 1):
                        if file.suffix.lower() == '.mp4':
                            shutil.move(file, v_folder / file.name)
                        elif file.suffix.lower() == '.jpg':
                            shutil.move(file, p_folder / file.name)
            
            # Add subdirectories to next level (except V and P folders)
            for item in current_dir.iterdir():
                if item.is_dir() and item.name not in ['V', 'P']:
                    next_level.append(item)
        
        # Move to next level
        current_level = next_level
    
    

def rename_files(output_dir: Path):
    # Helper function to get padded number string
    def get_padded_number(num: int, total_files: int) -> str:
        # Calculate required width based on total number of files
        width = len(str(total_files))
        return str(num).zfill(width)
    
    # Process each directory level
    folders = deque([output_dir])
    while folders:
        folder = folders.popleft()
        current_level_files = [f for f in folder.iterdir() if f.is_file()]
        for idx, f in enumerate(current_level_files, 1):
            new_name = f.name
            if folder.name == "P":
                new_name = f"P({get_padded_number(idx, len(current_level_files))}).jpg"
            elif folder.name == "V":
                new_name = f"V({get_padded_number(idx, len(current_level_files))}).mp4"
            else:
                new_name = f"preview({get_padded_number(idx, len(current_level_files))}){f.suffix.lower()}"
            f.rename(folder / new_name)
        folders += [f for f in folder.iterdir() if f.is_dir()]

# convert folder names and file names from simplified    chinese to traditional chinese
def convert_names(output_dir: Path):
    def convert_path(path: Path):
        # First recursively process directories
        if path.is_dir():
            # Get list of items before processing to avoid iterator issues
            items = list(path.iterdir())
            for item in items:
                convert_path(item)
        
        # Then convert current path's name
        new_name = cc.convert(path.name)
        if new_name != path.name:  # Only rename if the name actually changed
            path.rename(path.parent / new_name)
    
    # Start conversion from the output directory
    convert_path(output_dir)

def clear_empty_folders(output_dir: Path):
    for dir_path in sorted(output_dir.rglob("*"), reverse=True):
        if dir_path.is_dir() and not any(dir_path.iterdir()):
            dir_path.rmdir()

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

    convert_names(output_dir)
    organize_files(output_dir)
    rename_files(output_dir)
    clear_empty_folders(output_dir)


if __name__ == "__main__":
    main()