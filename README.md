# Image and Video Organizer

A Python script to organize and optimize images and videos for web use while preserving directory structure.

## Features

- **Video Optimization**:
  - Converts videos to MP4 format with H264 encoding
  - Optimizes for web streaming with `movflags=+faststart`
  - Scales down to 720p if larger (maintains original size if smaller)
  - Uses CRF 21 for high-quality compression
  - 128k AAC audio

- **Image Optimization**:
  - Converts images to JPEG format
  - Progressive JPEG for better web loading
  - 85% quality for good balance between size and quality
  - Optimized file size
  - Proper handling of transparent images

- **Directory Structure**:
  - Preserves original folder structure
  - Creates `_original` and `_converted` directories
  - Maintains file organization

## Requirements

```bash
pip install ffmpeg-python Pillow
```

Also requires FFmpeg to be installed on your system:
- macOS: `brew install ffmpeg`
- Ubuntu: `sudo apt install ffmpeg`
- Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

## Usage

1. Place your media files in the `_original` directory (create if it doesn't exist)
2. Run the script:
   ```bash
   python main.py
   ```
3. Find your optimized files in the `_converted` directory with the same structure

## Directory Structure

```
.
├── _original/          # Place your original files here
│   ├── folder1/
│   │   ├── video.mp4
│   │   └── image.jpg
│   └── folder2/
│       └── ...
├── _converted/         # Optimized files will be here
│   ├── folder1/
│   │   ├── video.mp4
│   │   └── image.jpg
│   └── folder2/
│       └── ...
└── main.py
```
