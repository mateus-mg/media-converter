# Installation

## System Dependencies

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install ffmpeg imagemagick
```

### Fedora/RHEL

```bash
sudo dnf install ffmpeg ImageMagick
```

### macOS

```bash
brew install ffmpeg imagemagick
```

## Python Environment

```bash
git clone https://github.com/mateus/media-converter.git
cd media-converter
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pillow pillow-heif python-dotenv
```

## Global Command Installation

```bash
./media-converter --install
source ~/.bashrc
converter /path/to/photos
```

## Verify Installation

```bash
converter check-deps
converter hw-accel
converter
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ffmpeg: command not found` | Install ffmpeg (see system dependencies) |
| Pillow import error | Run `pip install pillow pillow-heif` |
| HEIC conversion fails | Install ImageMagick as fallback |
| NVENC not detected | Check NVIDIA driver: `nvidia-smi` |