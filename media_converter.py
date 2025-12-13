#!/usr/bin/env python3
"""
Universal HEIC & HEVC Converter
Converts HEIC/HEIF images to JPEG 95% (or PNG) and H.265/HEVC videos to H.264 (maximum compatibility)
Compatible with files from smartphones, GoPro, and other devices.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import argparse


class Color:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    MAGENTA = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color


def print_info(msg: str) -> None:
    print(f"{Color.BLUE}[INFO]{Color.NC} {msg}")


def print_warn(msg: str) -> None:
    print(f"{Color.YELLOW}[WARN]{Color.NC} {msg}")


def print_error(msg: str) -> None:
    print(f"{Color.RED}[ERROR]{Color.NC} {msg}")


def print_success(msg: str) -> None:
    print(f"{Color.GREEN}[SUCCESS]{Color.NC} {msg}")


def check_dependencies() -> bool:
    """Check if required dependencies are installed"""
    # Check ffmpeg and ffprobe
    if not shutil.which('ffmpeg'):
        print_error("Missing dependency: ffmpeg")
        print("\nInstall with:")
        print("  sudo apt update && sudo apt install ffmpeg imagemagick")
        return False

    if not shutil.which('ffprobe'):
        print_error("Missing dependency: ffprobe (part of ffmpeg)")
        print("\nInstall with:")
        print("  sudo apt update && sudo apt install ffmpeg imagemagick")
        return False


def check_hardware_acceleration() -> str:
    """
    Detect hardware acceleration support
    Returns: 'qsv' (Intel Quick Sync), 'nvenc' (NVIDIA), 'vaapi' (generic), or 'none'
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-hide_banner', '-encoders'],
            capture_output=True,
            text=True,
            timeout=5
        )
        encoders = result.stdout

        # Prioridade: QSV > NVENC > VAAPI
        # Testar QSV (Intel Quick Sync)
        if 'h264_qsv' in encoders:
            test = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=1',
                 '-c:v', 'h264_qsv', '-f', 'null', '-'],
                capture_output=True,
                timeout=3
            )
            if test.returncode == 0:
                return 'qsv'

        # Testar NVENC (NVIDIA)
        if 'h264_nvenc' in encoders:
            test = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=1',
                 '-c:v', 'h264_nvenc', '-f', 'null', '-'],
                capture_output=True,
                timeout=3
            )
            if test.returncode == 0:
                return 'nvenc'

        # Testar VAAPI (genérico Linux)
        if 'h264_vaapi' in encoders:
            test = subprocess.run(
                ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=1',
                 '-vaapi_device', '/dev/dri/renderD128',
                 '-vf', 'format=nv12,hwupload', '-c:v', 'h264_vaapi', '-f', 'null', '-'],
                capture_output=True,
                timeout=3
            )
            if test.returncode == 0:
                return 'vaapi'

        return 'none'
    except Exception:
        return 'none'


def check_dependencies() -> bool:
    """Verifica se as dependências necessárias estão instaladas"""
    # Verificar ffmpeg e ffprobe
    if not shutil.which('ffmpeg'):
        print_error("Dependência faltando: ffmpeg")
        print("\nInstale com:")
        print("  sudo apt update && sudo apt install ffmpeg imagemagick")
        return False

    if not shutil.which('ffprobe'):
        print_error("Dependência faltando: ffprobe (parte do ffmpeg)")
        print("\nInstale com:")
        print("  sudo apt update && sudo apt install ffmpeg")
        return False

    # Verificar ImageMagick (magick para v7+ ou convert para v6)
    if not shutil.which('magick') and not shutil.which('convert'):
        print_error("Dependência faltando: imagemagick")
        print("\nInstale com:")
        print("  sudo apt update && sudo apt install imagemagick")
        print("\nOu via pip para bibliotecas Python (opcional para melhor qualidade):")
        print("  pip install pillow pillow-heif")
        return False

    return True


def count_files(directory: Path) -> Dict[str, int]:
    """Count files by extension"""
    counts = {'heic': 0, 'heif': 0, 'mov': 0, 'mp4': 0, 'aae': 0}

    for ext in counts.keys():
        counts[ext] = len(list(directory.rglob(f"*.{ext}"))) + \
            len(list(directory.rglob(f"*.{ext.upper()}")))

    return counts


def preserve_metadata(source: Path, destination: Path) -> None:
    """Preserve modification date from the original file"""
    try:
        stat_info = source.stat()
        os.utime(destination, (stat_info.st_atime, stat_info.st_mtime))
    except Exception as e:
        print_warn(f"Não foi possível preservar metadata: {e}")


def remove_aae_files(directory: Path, dry_run: bool = False) -> Dict[str, int]:
    """Remove .AAE files (Apple editing metadata)"""
    stats = {'deleted': 0, 'failed': 0}

    print_info("\n=== REMOVING .AAE FILES ===")

    aae_files = list(directory.rglob('*.aae')) + list(directory.rglob('*.AAE'))

    if not aae_files:
        print_info("No .AAE files found.")
        return stats

    print_info(f"Found {len(aae_files)} .AAE file(s)")

    for aae_file in sorted(aae_files):
        if dry_run:
            print_info(f"[DRY RUN] Would delete: {aae_file.name}")
            stats['deleted'] += 1
        else:
            try:
                print_info(f"Deleting: {aae_file.name}")
                aae_file.unlink()
                stats['deleted'] += 1
                print_success(f"Deleted: {aae_file.name}")
            except Exception as e:
                print_error(f"Error deleting {aae_file.name}: {e}")
                stats['failed'] += 1

    return stats


def convert_image_pillow(input_path: Path, output_format: str = 'PNG') -> Tuple[bool, Path]:
    """
    Converts HEIC/HEIF image using Pillow (lossless)
    PNG is used instead of JPEG to avoid quality loss
    """
    try:
        from PIL import Image
        from pillow_heif import register_heif_opener
        register_heif_opener()

        ext = '.png' if output_format.upper() == 'PNG' else '.jpg'
        output_path = input_path.with_suffix(ext)

        if output_path.exists():
            print_warn(f"File already exists: {output_path.name}")
            return False, output_path

        print_info(f"Converting: {input_path.name} → {output_path.name}")

        with Image.open(input_path) as img:
            # Apply EXIF orientation automatically
            if hasattr(img, '_getexif') and img._getexif() is not None:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)

            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            # Save with maximum quality and proper resize filter
            if output_format.upper() == 'PNG':
                # PNG: maximum lossless compression (reduces size without quality loss)
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            else:
                # JPEG: quality 95 (great quality/size balance)
                img.save(output_path, 'JPEG', quality=95,
                         subsampling=0, optimize=True)

        preserve_metadata(input_path, output_path)
        print_success(f"Converted: {output_path.name}")
        return True, output_path

    except ImportError:
        print_warn("Pillow/pillow-heif not available, using ImageMagick")
        return False, input_path
    except Exception as e:
        print_error(f"Error converting with Pillow: {e}")
        return False, input_path


def convert_image_imagemagick(input_path: Path, output_format: str = 'PNG') -> Tuple[bool, Path]:
    """
    Converts image using ImageMagick (fallback)
    """
    ext = '.png' if output_format.upper() == 'PNG' else '.jpg'
    output_path = input_path.with_suffix(ext)

    if output_path.exists():
        print_warn(f"File already exists: {output_path.name}")
        return False, output_path

    print_info(f"Converting: {input_path.name} → {output_path.name}")

    try:
        # Detectar qual comando usar (magick para v7+ ou convert para v6)
        imagemagick_cmd = 'magick' if shutil.which('magick') else 'convert'

        if output_format.upper() == 'PNG':
            # PNG com compressão lossless máxima (reduz tamanho sem perder qualidade)
            cmd = [
                imagemagick_cmd, str(input_path),
                '-auto-orient',
                '-filter', 'Lanczos',
                '-define', 'png:compression-level=9',
                '-define', 'png:compression-filter=5',
                '-define', 'png:compression-strategy=1',
                '-quality', '95',
                str(output_path)
            ]
        else:
            # JPEG com qualidade 95 (ótimo balanço qualidade/tamanho)
            cmd = [
                imagemagick_cmd, str(input_path),
                '-quality', '95',
                '-auto-orient',
                '-filter', 'Lanczos',
                '-sampling-factor', '4:2:0',
                str(output_path)
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            preserve_metadata(input_path, output_path)
            print_success(f"Converted: {output_path.name}")
            return True, output_path
        else:
            print_error(f"Conversion failed: {input_path.name}")
            if output_path.exists():
                output_path.unlink()
            return False, input_path

    except Exception as e:
        print_error(f"Error converting: {e}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path


def convert_image(input_path: Path, use_png: bool = False) -> Tuple[bool, Path]:
    """
    Converts HEIC/HEIF image to JPEG 95% (default) or PNG (lossless)
    Tries Pillow first, then ImageMagick as fallback
    """
    output_format = 'PNG' if use_png else 'JPEG'

    # Tentar com Pillow primeiro (melhor qualidade)
    success, output_path = convert_image_pillow(input_path, output_format)

    # Se Pillow falhar, usar ImageMagick
    if not success and not output_path.exists():
        success, output_path = convert_image_imagemagick(
            input_path, output_format)

    return success, output_path


def get_video_info(input_path: Path) -> Dict:
    """Get detailed video information"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(input_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception as e:
        print_warn(f"Error getting video info: {e}")

    return {}


def convert_video(input_path: Path, codec: str = 'h265', quality: str = 'high', resize: str = 'none') -> Tuple[bool, Path]:
    """
    Converts video with maximum quality preserved

    Codec options:
    - h265 (HEVC): Best compression, superior quality, smaller files
    - h264: Most compatible, excellent quality (RECOMMENDED for maximum compatibility)
    - copy: Remux only (no re-encoding)

    Quality options:
    - lossless: Lossless (very large files)
    - high: CRF 18 (visually lossless)
    - medium: CRF 23 (good quality)
    """
    output_path = input_path.with_suffix('.mp4')

    if output_path.exists():
        print_warn(f"File already exists: {output_path.name}")
        return False, output_path

    print_info(f"Converting video: {input_path.name}")

    # Get video information
    video_info = get_video_info(input_path)

    # Detect resolution
    width = 0
    height = 0
    duration = 0
    if video_info and 'streams' in video_info:
        for stream in video_info['streams']:
            if stream.get('codec_type') == 'video':
                width = stream.get('width', 0)
                height = stream.get('height', 0)
                break
        if 'format' in video_info:
            duration = float(video_info['format'].get('duration', 0))

    # Warn if 4K (will take a while)
    if height >= 2160:
        file_size = input_path.stat().st_size / (1024 * 1024)
        print_warn(
            f"  4K video detected ({width}x{height})! Size: {file_size:.1f} MB")
        print_warn(
            f"  Estimated time: {duration * 0.5:.0f}-{duration * 1:.0f} minutes")
        if resize == 'none':
            print_info(
                f"  Tip: Use --resize 2k to convert 3-4x faster")

    # Determinar resolução de saída
    scale_filter = []
    if resize != 'none' and resize != '4k':
        target_height = 1440 if resize in ['2k', '1440p'] else 1080

        # Só redimensiona se o vídeo for MAIOR que o alvo
        if height > target_height:
            scale_filter = [
                '-vf', f'scale=-2:{target_height}:flags=lanczos,scale=trunc(iw/2)*2:trunc(ih/2)*2']
            print_info(
                f"  Redimensionando: {width}x{height} → altura {target_height}px")
        else:
            # Vídeo já é menor ou igual, não redimensiona
            print_info(
                f"  Mantendo resolução original: {width}x{height} (já é ≤ {target_height}px)")

    # Forçar H.264 para vídeos de celulares (melhor compatibilidade)
    # HEVC de celulares pode ter problemas de reprodução em alguns players
    use_h264 = True

    # Detectar aceleração de hardware
    hw_accel = check_hardware_acceleration()

    # Ajustar qualidade automaticamente baseado na resolução
    # Vídeos maiores (4K, 2K) usam CRF mais alto para economizar espaço
    # Vídeos menores (1080p ou menos) podem usar CRF mais baixo
    auto_crf = None
    if quality == 'high':
        if height >= 2160:  # 4K
            auto_crf = '23'  # Qualidade boa, arquivo menor
            print_info(
                f"  Qualidade ajustada: CRF 23 (4K - otimizado para tamanho)")
        elif height >= 1440:  # 2K
            auto_crf = '20'  # Qualidade alta
            print_info(f"  Qualidade ajustada: CRF 20 (2K - alta qualidade)")
        else:  # 1080p ou menor
            auto_crf = '18'  # Qualidade muito alta
            print_info(
                f"  Qualidade ajustada: CRF 18 (≤1080p - máxima qualidade)")
    else:
        # quality == 'medium'
        auto_crf = '23'

    # Configurar codec de vídeo com aceleração de hardware se disponível
    if use_h264 or codec == 'h264':
        if hw_accel == 'qsv':
            # Intel Quick Sync Video (2-5x mais rápido)
            print_info(
                "  Usando Intel Quick Sync Video (aceleração de hardware)")
            video_codec = [
                '-c:v', 'h264_qsv',
                '-global_quality', auto_crf,
                '-preset', 'medium',
                '-profile:v', 'high'
            ]
        elif hw_accel == 'nvenc':
            # NVIDIA NVENC
            print_info("  Usando NVIDIA NVENC (aceleração de hardware)")
            video_codec = [
                '-c:v', 'h264_nvenc',
                '-cq', auto_crf,
                '-preset', 'p4',  # p4 = medium quality
                '-profile:v', 'high'
            ]
        elif quality == 'lossless':
            video_codec = ['-c:v', 'libx264', '-qp', '0', '-preset', 'medium']
        else:
            # Software encoding (sem aceleração)
            video_codec = [
                '-c:v', 'libx264',
                '-crf', auto_crf,
                '-preset', 'medium',  # medium é mais rápido que slow
                '-profile:v', 'high',
                '-level', '4.1'
            ]
    elif codec == 'h265':
        if quality == 'lossless':
            video_codec = ['-c:v', 'libx265', '-x265-params',
                           'lossless=1', '-preset', 'slower']
        else:
            crf = '18' if quality == 'high' else '23'
            video_codec = [
                '-c:v', 'libx265',
                '-crf', crf,
                '-preset', 'slower',
                '-x265-params', 'log-level=error'
            ]
    else:
        video_codec = ['-c:v', 'copy']

    # Configurar codec de áudio (AAC alta qualidade)
    if quality == 'lossless':
        audio_codec = ['-c:a', 'flac']
    else:
        audio_codec = ['-c:a', 'aac', '-b:a', '256k', '-ar', '48000']

    # Construir comando FFmpeg
    cmd = [
        'ffmpeg',
        '-i', str(input_path),
        '-progress', 'pipe:1',  # Mostrar progresso
        *video_codec,
        *scale_filter,  # Aplicar redimensionamento se necessário
        *audio_codec,
        '-movflags', '+faststart',
        '-map_metadata', '0',
        '-pix_fmt', 'yuv420p',  # Compatibilidade
        '-y',  # Sobrescrever sem perguntar
        str(output_path)
    ]

    print_info(
        f"  Codec: H.264 | CRF: {auto_crf if quality != 'lossless' else 'lossless'} | Preset: medium")
    if height >= 2160:
        print_info(f"  Processando vídeo 4K... Aguarde, isso vai demorar!")
    else:
        print_info(f"  Convertendo... (alguns minutos)")

    import time
    start_time = time.time()

    try:
        # 60 min timeout para 4K
        result = subprocess.run(cmd, capture_output=True,
                                text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        print_error(f"Timeout ao converter vídeo (60 min): {input_path.name}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path

    elapsed_time = time.time() - start_time

    if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
        preserve_metadata(input_path, output_path)

        # Mostrar comparação de tamanhos
        original_size = input_path.stat().st_size / (1024 * 1024)
        converted_size = output_path.stat().st_size / (1024 * 1024)
        ratio = (converted_size / original_size) * 100

        print_success(f"Convertido: {output_path.name}")
        print_info(
            f"  Original: {original_size:.2f} MB | Convertido: {converted_size:.2f} MB ({ratio:.1f}%)")
        return True, output_path
    else:
        print_error(f"Erro ao converter vídeo: {input_path.name}")
        if result.stderr:
            # Últimos 200 chars do erro
            print_error(f"  {result.stderr[-200:]}")
        if output_path.exists():
            output_path.unlink()
        return False, input_path


def process_directory(
    directory: Path,
    image_format: str = 'PNG',
    video_codec: str = 'h265',
    video_quality: str = 'high',
    dry_run: bool = False,
    delete_originals: bool = False,
    resize: str = 'none',
    only_images: bool = False,
    only_videos: bool = False,
    only_hevc_videos: bool = False
) -> Tuple[Dict[str, int], List[Path]]:
    """Processa todos os arquivos no diretório"""
    stats = {
        'images_converted': 0,
        'videos_converted': 0,
        'images_failed': 0,
        'videos_failed': 0,
        'images_skipped': 0,
        'videos_skipped': 0
    }

    # Lista de arquivos originais convertidos com sucesso
    converted_originals = []
    # Lista de imagens originais que já possuem arquivo convertido
    already_converted_images = []

    # Processar imagens (se não for only_videos)
    if not only_videos:
        print_info("\n=== PROCESSANDO IMAGENS ===")
        image_extensions = ['*.heic', '*.HEIC', '*.heif', '*.HEIF']
    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.rglob(ext))

    for img_file in sorted(image_files):
        # Verificar se já existe arquivo convertido (mesmo nome, extensão .jpg ou .png)
        jpg_path = img_file.with_suffix('.jpg')
        png_path = img_file.with_suffix('.png')
        if jpg_path.exists() or png_path.exists():
            stats['images_skipped'] += 1
            already_converted_images.append(img_file)
            continue
        if dry_run:
            print_info(f"[DRY RUN] Converteria: {img_file.name}")
            stats['images_converted'] += 1
        else:
            # Sempre usar JPEG 95% (use_png=False)
            success, _ = convert_image(img_file, use_png=False)
            if success:
                stats['images_converted'] += 1
                converted_originals.append(img_file)
            elif _.exists():
                stats['images_skipped'] += 1
            else:
                stats['images_failed'] += 1

    # Process videos (if not only_images)
    if not only_images:
        print_info("\n=== PROCESSING VIDEOS ===")
        video_extensions = ['*.mov', '*.MOV', '*.mp4', '*.MP4']
        video_files = []
        for ext in video_extensions:
            video_files.extend(directory.rglob(ext))

        for vid_file in sorted(video_files):
            # Skip already converted files
            if '_converted' in vid_file.stem:
                continue

            # Detect codec if needed
            if only_hevc_videos:
                info = get_video_info(vid_file)
                codec_name = None
                if info and 'streams' in info:
                    for stream in info['streams']:
                        if stream.get('codec_type') == 'video':
                            codec_name = stream.get('codec_name')
                            break
                if codec_name != 'hevc':
                    print_info(
                        f"Skipping {vid_file.name}: codec {codec_name or 'unknown'} (not HEVC/H.265)")
                    stats['videos_skipped'] += 1
                    continue

            if dry_run:
                print_info(f"[DRY RUN] Would convert: {vid_file.name}")
                stats['videos_converted'] += 1
            else:
                success, _ = convert_video(
                    vid_file, codec=video_codec, quality=video_quality, resize=resize)
                if success:
                    stats['videos_converted'] += 1
                    converted_originals.append(vid_file)
                elif _.exists():
                    stats['videos_skipped'] += 1
                else:
                    stats['videos_failed'] += 1

    # Also return already converted images for possible deletion
    return stats, converted_originals + already_converted_images


def install_command() -> int:
    """Installs the 'converter' command globally on the system"""
    script_dir = Path(__file__).parent.absolute()
    wrapper_path = script_dir / 'converter'
    alias_line = f"alias converter='{wrapper_path}'"
    bashrc_path = Path.home() / '.bashrc'

    print("\n" + "=" * 60)
    print("  INSTALLING 'converter' COMMAND")
    print("=" * 60 + "\n")

    # Check if wrapper exists
    if not wrapper_path.exists():
        print_error(f"Wrapper file not found: {wrapper_path}")
        print_info("Run the script normally first to create it.")
        return 1

    # Check if already exists
    if bashrc_path.exists():
        with open(bashrc_path, 'r') as f:
            content = f.read()
            if 'alias converter=' in content:
                print_info("Alias 'converter' already exists in ~/.bashrc")
                print_info("Updating...")
                # Remove old lines
                lines = content.split('\n')
                lines = [line for line in lines if 'alias converter=' not in line]
                content = '\n'.join(lines)
                with open(bashrc_path, 'w') as fw:
                    fw.write(content)

    # Add new alias
    with open(bashrc_path, 'a') as f:
        f.write(f"\n# Media Converter\n{alias_line}\n")

    print_success("Alias added to ~/.bashrc")
    print()
    print("=" * 60)
    print(f"{Color.GREEN}  INSTALLATION COMPLETE!{Color.NC}")
    print("=" * 60)
    print()
    print("To use now, run:")
    print(f"  {Color.CYAN}source ~/.bashrc{Color.NC}")
    print()
    print("Or close and reopen the terminal.")
    print()
    print("Then you can use it from anywhere:")
    print(f"  {Color.GREEN}converter /path/to/photos{Color.NC}")
    print(f"  {Color.GREEN}converter --help{Color.NC}")
    print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='Media Converter for Universal Formats with Maximum Quality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
    %(prog)s /path/to/photos
    %(prog)s /path/to/photos --image-format jpeg --video-codec h264
    %(prog)s /path/to/photos --video-quality lossless
    %(prog)s /path/to/photos --resize 2k --video-quality medium
    %(prog)s /path/to/photos --dry-run

Image formats:
    PNG  - Lossless (recommended, larger files)
    JPEG - High quality with compression (smaller files)

Video codecs:
    h265 - HEVC, best compression and quality (recommended)
    h264 - H.264, more compatible
    copy - Remux only, no re-encoding

Video quality:
    lossless - Lossless (very large files)
    high     - CRF 18, visually lossless (recommended)
    medium   - CRF 23, good quality, smaller files

Video resizing:
    4k       - Keep original resolution (default)
    2k/1440p - 2560x1440 (best quality/speed balance)
    1080p    - 1920x1080 (faster, smaller size)
        """
    )
    parser.add_argument(
        '--only-hevc-videos',
        action='store_true',
        help='Process only videos encoded in H.265/HEVC (GoPro, smartphones, etc)'
    )
    parser.add_argument(
        'directory',
        nargs='?',
        type=Path,
        help='Directory containing files to convert'
    )
    parser.add_argument(
        '--image-format',
        choices=['PNG', 'JPEG', 'png', 'jpeg'],
        default='PNG',
        help='Output format for images (default: PNG)'
    )
    parser.add_argument(
        '--video-codec',
        choices=['h265', 'h264', 'copy'],
        default='h265',
        help='Codec for videos (default: h265/HEVC)'
    )
    parser.add_argument(
        '--video-quality',
        choices=['lossless', 'high', 'medium'],
        default='high',
        help='Video quality (default: high)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate conversion without processing files'
    )
    parser.add_argument(
        '--delete-originals',
        action='store_true',
        help='CAUTION: Delete original files after successful conversion'
    )
    parser.add_argument(
        '--remove-aae',
        action='store_true',
        help='Remove .AAE files (Apple editing metadata)'
    )
    parser.add_argument(
        '--resize',
        choices=['4k', '2k', '1440p', '1080p', 'none'],
        default='none',
        help='Resize videos: 4k (keep), 2k/1440p (2560x1440), 1080p (1920x1080)'
    )
    parser.add_argument(
        '--only-images',
        action='store_true',
        help='Process only images (HEIC/HEIF)'
    )
    parser.add_argument(
        '--only-videos',
        action='store_true',
        help='Process only videos (MOV/MP4)'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install \'converter\' command globally on the system'
    )

    args = parser.parse_args()

    # If install, run and exit
    if args.install:
        return install_command()

    # Banner
    print("\n" + "=" * 60)
    print("  UNIVERSAL HEIC & HEVC CONVERTER - MAXIMUM COMPATIBILITY")
    print("=" * 60 + "\n")

    # Check dependencies
    print_info("Checking dependencies...")
    if not check_dependencies():
        return 1

    # Check hardware acceleration
    hw_accel = check_hardware_acceleration()
    if hw_accel == 'qsv':
        print_success(
            "✓ Hardware acceleration: Intel Quick Sync Video detected!")
        print_info("  Video conversion will be 2-5x faster")
    elif hw_accel == 'nvenc':
        print_success("✓ Hardware acceleration: NVIDIA NVENC detected!")
        print_info("  Video conversion will be 3-5x faster")
    elif hw_accel == 'vaapi':
        print_success("✓ Hardware acceleration: VAAPI detected!")
        print_info("  Video conversion will be 2-3x faster")
    else:
        print_warn("⚠ Hardware acceleration not detected")
        print_info("  Conversion will use CPU (slower, but works)")

    print()  # Blank line

    print_success("All dependencies are installed!\n")

    # Get directory
    if args.directory:
        start_dir = args.directory
    else:
        dir_input = input(
            "Enter the folder path to search for files: ").strip()
        start_dir = Path(dir_input)

    # Validate directory
    if not start_dir.exists() or not start_dir.is_dir():
        print_error(f"Directory not found: {start_dir}")
        return 1

    # Count files
    print_info(
        f"Searching for HEIC/HEIF files and H.265/HEVC videos in: {start_dir}")
    file_counts = count_files(start_dir)
    total_files = sum(file_counts.values())

    if total_files == 0:
        print_warn("No HEIC, HEIF, MOV or MP4 files found.")
        return 0

    # Show filtered summary according to selected option
    print(f"\n{Color.CYAN}=== FILES FOUND ==={Color.NC}")
    shown_types = []
    if args.only_images:
        shown_types = ['heic', 'heif']
    elif args.only_videos:
        shown_types = ['mov', 'mp4']
    else:
        shown_types = ['heic', 'heif', 'mov', 'mp4']
    filtered_total = 0
    for ext in shown_types:
        count = file_counts.get(ext, 0)
        if count > 0:
            print(f"  {ext.upper()}: {count} file(s)")
            filtered_total += count
    print(f"  {Color.MAGENTA}TOTAL: {filtered_total} file(s){Color.NC}\n")

    # Show settings
    print(f"{Color.CYAN}=== SETTINGS ==={Color.NC}")
    print(f"  Image format: JPEG 95%")
    print(f"  Video codec: H.264")
    print(f"  Video quality: {args.video_quality.upper()}")
    if args.resize != 'none':
        print(f"  Resize videos: {args.resize.upper()}")
    if args.dry_run:
        print(f"  {Color.YELLOW}DRY RUN MODE (simulation){Color.NC}")
    print()

    # Show actions and selected mode
    print(f"{Color.CYAN}=== ACTIONS TO BE PERFORMED ==={Color.NC}")
    if args.only_images:
        print(f"  • MODE: Only images will be converted (HEIC/HEIF → JPEG 95%)")
        print(f"  • MOV/MP4 will be ignored")
    elif args.only_videos:
        print(f"  • MODE: Only videos will be converted (MOV/MP4 → H.264)")
        print(f"  • HEIC/HEIF will be ignored")
    else:
        print(f"  • HEIC/HEIF → JPEG 95% (great quality/size balance)")
        print(f"  • MOV/MP4 → H.264 (maximum compatibility)")

    quality_desc = {
        'lossless': 'truly lossless (very large files)',
        'high': 'CRF 18 - visually lossless (recommended)',
        'medium': 'CRF 23 - good quality, smaller size'
    }
    print(f"  • Quality: {quality_desc[args.video_quality]}")
    if args.resize != 'none':
        resize_desc = {
            '4k': 'keep 4K',
            '2k': 'max 1440p (2K)',
            '1440p': 'max 1440p (2K)',
            '1080p': 'max 1080p (Full HD)'
        }
        print(
            f"  • Resizing: {resize_desc.get(args.resize, args.resize)}")
    print(f"  • Automatic EXIF orientation correction")
    print(f"  • Metadata and original date preservation")
    print()

    # Confirm
    if not args.dry_run:
        confirm = input(
            f"Proceed with conversion? (y/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print_info("Conversion cancelled by user.")
            return 0
        print()

    # Process files
    print_info("Starting conversion...\n")
    stats, converted_files = process_directory(
        start_dir,
        image_format=args.image_format,
        video_codec=args.video_codec,
        video_quality=args.video_quality,
        dry_run=args.dry_run,
        delete_originals=args.delete_originals,
        resize=args.resize,
        only_images=args.only_images,
        only_videos=args.only_videos,
        only_hevc_videos=args.only_hevc_videos
    )

    # Check and ask about .AAE files
    aae_stats = None
    if not args.dry_run:
        # Count .AAE files
        aae_files = list(start_dir.rglob('*.AAE')) + \
            list(start_dir.rglob('*.aae'))

        if aae_files:
            print(f"\n{Color.CYAN}=== .AAE FILES FOUND ==={Color.NC}")
            print_info(
                f"Found {len(aae_files)} Apple .AAE metadata file(s)")
            print_info(
                "These files contain edits made in the Photos app on your phone")

            confirm_aae = input(
                f"{Color.YELLOW}Delete .AAE files? (type 'YES' in uppercase): {Color.NC}").strip()

            if confirm_aae == 'YES':
                aae_stats = remove_aae_files(start_dir, dry_run=False)
            else:
                print_info(".AAE files preserved.")
    elif args.remove_aae:
        # Dry-run mode with --remove-aae explicitly
        aae_stats = remove_aae_files(start_dir, dry_run=True)

    # Ask about deleting original files
    if converted_files and not args.dry_run:
        print(f"\n{Color.CYAN}=== ORIGINAL FILES ==={Color.NC}")
        print_info(
            f"{len(converted_files)} file(s) were successfully converted")

        confirm_delete = input(
            f"{Color.RED}Delete original files? (type 'YES' in uppercase): {Color.NC}").strip()

        if confirm_delete == 'YES':
            deleted_count = 0
            failed_delete = 0

            for original_file in converted_files:
                try:
                    print_info(f"Deleting: {original_file.name}")
                    original_file.unlink()
                    deleted_count += 1
                    print_success(f"Deleted: {original_file.name}")
                except Exception as e:
                    print_error(f"Error deleting {original_file.name}: {e}")
                    failed_delete += 1

            print(f"\n{Color.GREEN}Files deleted:{Color.NC} {deleted_count}")
            if failed_delete > 0:
                print(f"{Color.RED}Failed to delete:{Color.NC} {failed_delete}")
        else:
            print_info("Original files preserved.")
    elif args.delete_originals and converted_files and not args.dry_run:
        # --delete-originals used explicitly (force delete)
        print(f"\n{Color.CYAN}=== DELETING ORIGINAL FILES ==={Color.NC}")
        deleted_count = 0
        failed_delete = 0

        for original_file in converted_files:
            try:
                print_info(f"Deleting: {original_file.name}")
                original_file.unlink()
                deleted_count += 1
                print_success(f"Deleted: {original_file.name}")
            except Exception as e:
                print_error(f"Error deleting {original_file.name}: {e}")
                failed_delete += 1

        print(f"\n{Color.GREEN}Files deleted:{Color.NC} {deleted_count}")
        if failed_delete > 0:
            print(f"{Color.RED}Failed to delete:{Color.NC} {failed_delete}")
    elif args.delete_originals and not converted_files:
        print_warn("No files were converted, nothing to delete.")

    # Final report
    print(f"\n{Color.CYAN}{'=' * 60}{Color.NC}")
    print_success("CONVERSION COMPLETE!")
    print(f"{Color.CYAN}{'=' * 60}{Color.NC}\n")

    print(
        f"{Color.GREEN}Images converted:{Color.NC} {stats['images_converted']}")
    print(
        f"{Color.GREEN}Videos converted:{Color.NC} {stats['videos_converted']}" )

    if aae_stats:
        print(
            f"{Color.GREEN}.AAE files deleted:{Color.NC} {aae_stats['deleted']}")

    if stats['images_skipped'] > 0:
        print(
            f"{Color.YELLOW}Images already exist (skipped):{Color.NC} {stats['images_skipped']}")
    if stats['videos_skipped'] > 0:
        print(
            f"{Color.YELLOW}Videos already exist (skipped):{Color.NC} {stats['videos_skipped']}")

    if stats['images_failed'] > 0:
        print(
            f"{Color.RED}Images with error:{Color.NC} {stats['images_failed']}")
    if stats['videos_failed'] > 0:
        print(
            f"{Color.RED}Videos with error:{Color.NC} {stats['videos_failed']}")
    if aae_stats and aae_stats['failed'] > 0:
        print(
            f"{Color.RED}.AAE files with error:{Color.NC} {aae_stats['failed']}")

    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warn("\n\nConversion interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
