

# Universal HEIC & HEVC Converter

![GitHub release (latest by date)](https://img.shields.io/github/v/release/mateus-mg/media_converter?label=version&style=flat-square)

Converts HEIC/HEIF images to JPEG 95% (or PNG) and H.265/HEVC videos to H.264 (maximum compatibility). Compatible with files from iOS, GoPro, and other devices.

## 🚀 Installation

### 1. System Dependencies
```bash
sudo apt update && sudo apt install ffmpeg imagemagick
```

### 2. Install Python Packages (optional, but recommended)
```bash
# Activate virtual environment
source venv/bin/activate

# Install Python dependencies for best quality
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Install Global Command (optional)
```bash
./media_converter.py --install
source ~/.bashrc
```

Now you can use `converter` from anywhere!

## 📖 Usage

### Option 1: Global Command (after installation)
```bash
media_converter.py /path/to/photos
media_converter.py ~/Downloads --delete-originals
media_converter.py --help
```

### Option 2: Run Directly
```bash
cd /media/mateus/Servidor/scripts/media-converter
source venv/bin/activate
./media_converter.py /path/to/photos
```

### Usage Examples

**Basic (interactive mode):**
```bash
media_converter.py
```

**With arguments:**
```bash
# Convert a specific folder
media_converter.py /path/to/photos

# With lossless quality
media_converter.py /path/to/photos --video-quality lossless

# Convert to PNG instead of JPEG (default is JPEG)
media_converter.py /path/to/photos --image-format PNG

# Convert only images (HEIC/HEIF → JPEG 95%)
media_converter.py /path/to/photos --only-images

# Convert only videos (MOV/MP4 → H.264/H.265)
media_converter.py /path/to/photos --only-videos

# Convert only videos encoded in H.265/HEVC (GoPro, iOS, etc)
media_converter.py /path/to/photos --only-hevc-videos

# Convert only images to JPEG, removing originals and .AAE files
media_converter.py /path/to/photos --only-images --image-format jpeg --delete-originals --remove-aae

# Delete original files after conversion (CAUTION!)
media_converter.py /path/to/photos --delete-originals

# Simulate without converting
media_converter.py /path/to/photos --dry-run
```

## ⚙️ Available Options

**Image Formats:**
- `--image-format JPEG` - High quality with compression (default, recommended)
- `--image-format PNG` - Lossless (larger files)
**Selective processing:**
- `--only-images` - Process only images (HEIC/HEIF)
- `--only-videos` - Process only videos (MOV/MP4)
- `--only-hevc-videos` - Process only videos encoded in H.265/HEVC (GoPro, iOS, etc)
**About image conversion:**
- The script tries to use Pillow (with pillow-heif) for image conversion, ensuring maximum quality and metadata preservation. If not available, it uses ImageMagick as a fallback.
- The default output format for images is JPEG 95% (great quality/size balance). Use `--image-format PNG` for lossless output.

**Video Codecs:**
- `--video-codec h265` - HEVC, better compression and quality (default)
- `--video-codec h264` - H.264, more compatible
- `--video-codec copy` - Remux only, no re-encoding

**Video Quality:**
- `--video-quality lossless` - Lossless (very large files)
- `--video-quality high` - CRF 18, visually lossless (default)
- `--video-quality medium` - CRF 23, good quality, smaller size

**Other Options:**
- `--dry-run` - Simulate without converting
- `--delete-originals` - Delete originals after successful conversion

## 🛡️ Safety

- Only deletes files if conversion is successful
- Files with errors are preserved
- Double confirmation required for deletion
- Preserves metadata and original dates

## 🎯 Features

- ✅ Recursive conversion (searches subfolders)
- ✅ Selective processing: only images, only videos, or only HEVC videos
- ✅ Compatible with files from iOS, GoPro, and other devices
- ✅ EXIF orientation preservation
- ✅ Metadata and date preservation
- ✅ Detailed conversion report
- ✅ Colorful and intuitive interface
- ✅ Protection against overwriting existing files
- ✅ Automatic fallback to ImageMagick if Pillow is not available

## 📝 About the Virtual Environment

If you activated the virtual environment manually with:
```bash
source venv/bin/activate
```
when finished, run:
```bash
deactivate
```

If you used the global command `converter` or ran the bash script `media_converter`, you do not need to run `deactivate`, as the script itself will activate and deactivate the virtual environment automatically.
