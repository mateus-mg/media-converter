#!/usr/bin/env python3
"""
CLI Manager for Media Converter System
Command-line interface for converting HEIC/HEIF images to JPEG/PNG and HEVC videos to H.264
"""

# Flexible import to handle direct execution and importing
try:
    from .log_config import get_logger, log_success, log_error, log_warning, log_info, log_convert, log_image, log_video
    from .log_formatter import format_conversion_session, format_conversion_start, format_conversion_complete, format_batch_summary, format_hardware_detection
except ImportError:
    # When executed directly, use absolute imports
    import sys
    from pathlib import Path
    # Add scripts directory to path
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))

    from log_config import get_logger, log_success, log_error, log_warning, log_info, log_convert, log_image, log_video
    from log_formatter import format_conversion_session, format_conversion_start, format_conversion_complete, format_batch_summary, format_hardware_detection

import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import SIMPLE
from rich.prompt import Prompt
import argparse


class CLIManager:
    """CLI manager for Media Converter System"""

    def __init__(self):
        """Initialize CLI manager"""
        self.script_dir = Path(os.getenv('SCRIPT_PATH', os.getcwd()))
        self.logs_dir = self.script_dir / 'logs'
        self.data_dir = self.script_dir / 'data'
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize logger
        self.logger = get_logger(__name__)

    def _get_media_converter(self):
        """Import media_converter from the scripts package."""
        try:
            from . import media_converter as media_converter_module
        except ImportError:
            # Fallback for direct execution
            import media_converter as media_converter_module
        return media_converter_module

    def show_interactive_menu(self):
        """Show interactive main menu"""
        while True:
            console.print("\n[bold cyan]🎬 Media Converter System[/bold cyan]")
            console.print("[bold]Select an operation:[/bold]")

            options = {
                "1": "Convert images (HEIC/HEIF)",
                "2": "Convert videos (HEVC/H.265)",
                "3": "Convert images and videos (batch)",
                "4": "Remove AAE files",
                "5": "View system status",
                "6": "View conversion logs",
                "7": "Check dependencies",
                "8": "View hardware acceleration",
                "9": "Exit"
            }

            for key, value in options.items():
                console.print(f"  [{key}] {value}")

            try:
                choice = Prompt.ask("\nYour choice", choices=list(
                    options.keys()), default="9")

                if choice == '1':
                    self.convert_single_image_interactive()
                elif choice == '2':
                    self.convert_single_video_interactive()
                elif choice == '3':
                    self.convert_both_interactive()
                elif choice == '4':
                    self.remove_aae_interactive()
                elif choice == '5':
                    self.show_status_interactive()
                elif choice == '6':
                    self.view_logs_interactive()
                elif choice == '7':
                    self.check_dependencies_interactive()
                elif choice == '8':
                    self.check_hardware_accel_interactive()
                elif choice == '9':
                    console.print("[green]Exiting... Goodbye![/green]")
                    break

                # Pause before showing the menu again
                input("\nPress Enter to continue...")

            except KeyboardInterrupt:
                console.print("\n[red]Operation cancelled by user.[/red]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def convert_single_image_interactive(self):
        """Interactive image conversion"""
        try:
            media_converter = self._get_media_converter()
            media_converter.run_interactive_conversion(
                preselected_mode="images")
        except Exception as e:
            log_error(self.logger, f"Error during image conversion: {str(e)}")

    def convert_single_video_interactive(self):
        """Interactive video conversion"""
        try:
            media_converter = self._get_media_converter()
            media_converter.run_interactive_conversion(
                preselected_mode="videos")
        except Exception as e:
            log_error(self.logger, f"Error during video conversion: {str(e)}")

    def convert_both_interactive(self):
        """Interactive conversion of both images and videos"""
        try:
            media_converter = self._get_media_converter()
            media_converter.run_interactive_conversion(preselected_mode=None)
        except Exception as e:
            log_error(self.logger, f"Error during batch conversion: {str(e)}")

    def remove_aae_interactive(self):
        """Interactive AAE file removal"""
        console.print("\n[bold cyan]🗑️  Remove AAE Files[/bold cyan]")

        try:
            input_dir = Prompt.ask("Enter directory to scan for AAE files")
            input_directory = Path(input_dir)

            if not input_directory.exists() or not input_directory.is_dir():
                log_error(
                    self.logger, f"Directory does not exist: {input_directory}")
                return

            # Count AAE files
            aae_files = list(input_directory.rglob("*.aae")) + \
                list(input_directory.rglob("*.AAE"))
            console.print(f"[green]Found {len(aae_files)} AAE files[/green]")

            if len(aae_files) == 0:
                console.print("[yellow]No AAE files found.[/yellow]")
                return

            confirm = Prompt.ask(
                f"Remove {len(aae_files)} AAE files? Type YES to continue",
                choices=["YES", "NO"],
                default="NO"
            )
            if confirm != "YES":
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

            # Remove AAE files
            removed = 0
            failed = 0

            for aae_file in aae_files:
                try:
                    aae_file.unlink()
                    removed += 1
                    console.print(f"[green]Removed: {aae_file.name}[/green]")
                except Exception as e:
                    log_error(
                        self.logger, f"Error removing {aae_file.name}: {str(e)}")
                    failed += 1

            log_success(
                self.logger, f"AAE cleanup completed: {removed} removed, {failed} failed")

        except Exception as e:
            log_error(self.logger, f"Error during AAE removal: {str(e)}")

    def show_status_interactive(self):
        """Show system status"""
        console.print("\n[bold cyan]📊 System Status[/bold cyan]")

        try:
            # Check dependencies
            console.print("\n[bold]Dependencies:[/bold]")
            deps_ok = self.check_dependencies()
            if deps_ok:
                console.print(
                    "[green]All dependencies are available[/green]")
            else:
                console.print("[red]Some dependencies are missing[/red]")

            # Check hardware acceleration
            console.print("\n[bold]Hardware Acceleration:[/bold]")
            hw_accel = self.check_hardware_acceleration()
            console.print(f"Detected: {hw_accel}")

            # Show disk space
            console.print("\n[bold]Disk Space:[/bold]")
            try:
                total, used, free = shutil.disk_usage(self.script_dir)
                console.print(f"Total: {total / (1024**3):.2f} GB")
                console.print(f"Used: {used / (1024**3):.2f} GB")
                console.print(f"Free: {free / (1024**3):.2f} GB")
            except Exception as e:
                console.print(f"[red]Error getting disk space: {str(e)}[/red]")

        except Exception as e:
            log_error(self.logger, f"Error getting system status: {str(e)}")

    def view_logs_interactive(self):
        """View conversion logs"""
        console.print("\n[bold cyan]📋 Conversion Logs[/bold cyan]")

        try:
            log_file = self.logs_dir / "media_converter.log"
            if not log_file.exists():
                console.print("[yellow]No log file found.[/yellow]")
                return

            lines = Prompt.ask("Number of lines to show",
                               default=50, choices=[10, 20, 50, 100])

            try:
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-int(lines):] if len(
                        all_lines) >= int(lines) else all_lines

                for line in last_lines:
                    console.print(line.rstrip())

            except Exception as e:
                console.print(f"[red]Error reading log file: {str(e)}[/red]")

        except Exception as e:
            log_error(self.logger, f"Error viewing logs: {str(e)}")

    def check_dependencies_interactive(self):
        """Check dependencies interactively"""
        console.print("\n[bold cyan]🔍 Check Dependencies[/bold cyan]")

        try:
            deps_ok = self.check_dependencies()

            if deps_ok:
                console.print(
                    "[green]All required dependencies are available:[/green]")
                console.print("  - ffmpeg")
                console.print("  - ffprobe")
                console.print("  - ImageMagick (magick or convert)")
                console.print("\n[green]Optional Python packages:[/green]")
                self.check_python_packages()
            else:
                console.print("[red]Some dependencies are missing[/red]")

        except Exception as e:
            log_error(self.logger, f"Error checking dependencies: {str(e)}")

    def check_hardware_accel_interactive(self):
        """Check hardware acceleration interactively"""
        console.print("\n[bold cyan]💻 Check Hardware Acceleration[/bold cyan]")

        try:
            hw_accel = self.check_hardware_acceleration()
            console.print(
                f"[green]Hardware acceleration detected: {hw_accel}[/green]")

            # Show capabilities
            if hw_accel != 'none':
                caps = self.get_hardware_capabilities(hw_accel)
                console.print("\n[bold]Capabilities:[/bold]")
                for key, value in caps.items():
                    console.print(f"  {key}: {value}")

        except Exception as e:
            log_error(
                self.logger, f"Error checking hardware acceleration: {str(e)}")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        try:
            media_converter = self._get_media_converter()
            return media_converter.check_dependencies()
        except Exception as e:
            log_error(self.logger, f"Error checking dependencies: {e}")
            return False

    def check_python_packages(self) -> bool:
        """Check if optional Python packages are installed"""
        try:
            media_converter = self._get_media_converter()
            return media_converter.check_python_packages()
        except Exception as e:
            log_error(self.logger, f"Error checking Python packages: {e}")
            return False

    def check_hardware_acceleration(self) -> str:
        """Detect hardware acceleration support"""
        try:
            media_converter = self._get_media_converter()
            return media_converter.check_hardware_acceleration()
        except Exception as e:
            log_error(
                self.logger, f"Error checking hardware acceleration: {e}")
            return 'none'

    def get_hardware_capabilities(self, hw_accel: str) -> dict:
        """Get detailed capabilities of hardware acceleration"""
        caps = {}

        try:
            result = subprocess.run(
                ['ffmpeg', '-hide_banner', '-encoders'],
                capture_output=True,
                text=True,
                timeout=5
            )
            encoders = result.stdout

            if hw_accel == 'nvenc':
                caps['encoder'] = 'NVIDIA NVENC'
                caps['supported_formats'] = 'h264, hevc'
                caps['presets'] = 'p1-p7 (p4 is balanced)'
            elif hw_accel == 'qsv':
                caps['encoder'] = 'Intel Quick Sync Video'
                caps['supported_formats'] = 'h264, hevc, vp9'
                caps['presets'] = 'veryfast, faster, fast, medium, slow, slower, veryslow'
            elif hw_accel == 'vaapi':
                caps['encoder'] = 'Video Acceleration API'
                caps['supported_formats'] = 'h264, hevc'
                caps['presets'] = 'varies by hardware'

        except Exception as e:
            log_error(self.logger, f"Error getting hardware capabilities: {e}")

        return caps

    def convert_image(self, input_path: Path, use_png: bool = False):
        """
        Converts HEIC/HEIF image to JPEG 95% (default) or PNG (lossless)
        Tries Pillow first, then ImageMagick as fallback
        """
        media_converter = self._get_media_converter()
        return media_converter.convert_image(input_path, use_png)

    def convert_video(self, input_path: Path, codec: str = 'h264', quality: str = 'high', resize: str = 'none'):
        """
        Converts video with maximum quality preserved
        """
        media_converter = self._get_media_converter()
        return media_converter.convert_video(input_path, codec, quality, resize)

    def is_hevc_video(self, video_path: Path) -> bool:
        """
        Check if video file uses HEVC codec
        """
        try:
            media_converter = self._get_media_converter()
            return media_converter.is_hevc_video(video_path)
        except Exception:
            return False

    def show_menu(self):
        """Show main menu with help information"""
        from rich.panel import Panel
        from rich.text import Text

        # Create a panel with the help information
        help_text = Text()
        help_text.append("Available commands:\n", style="bold cyan")
        help_text.append(
            "  convert-image <input> [format]    - Convert HEIC/HEIF to JPEG/PNG\n")
        help_text.append(
            "  convert-video <input> [options]   - Convert HEVC/H.265 to H.264\n")
        help_text.append(
            "  batch-convert <dir> [type]        - Batch convert directory\n")
        help_text.append(
            "  remove-aae <dir>                  - Remove AAE files\n")
        help_text.append(
            "  status                            - Show system status\n")
        help_text.append(
            "  logs                              - Show conversion logs\n")
        help_text.append(
            "  check-deps                        - Check dependencies\n")
        help_text.append(
            "  hw-accel                          - Check hardware acceleration\n")
        help_text.append(
            "  interactive                       - Start interactive menu\n")
        help_text.append(
            "  help                              - Show this help\n")
        help_text.append("\nExamples:\n", style="bold green")
        help_text.append("  media-converter interactive\n")
        help_text.append("  media-converter convert-image photo.HEIC JPEG\n")
        help_text.append(
            "  media-converter convert-video video.MOV h264 high\n")
        help_text.append("  media-converter batch-convert ./photos images\n")

        console.print(
            "\n[bold cyan]🎬 Media Converter System - CLI Manager[/bold cyan]\n")
        console.print(
            Panel(help_text, title="📖 Commands Help", border_style="blue"))


console = Console()


def main():
    """Main entry point"""
    cli_manager = CLIManager()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "interactive":
            cli_manager.show_interactive_menu()
        elif command == "help" or command == "--help" or command == "-h":
            cli_manager.show_menu()
        elif command == "convert-image":
            if len(sys.argv) < 3:
                console.print("[red]Error: Input file required[/red]")
                return
            # Handle convert-image command
            input_file = Path(sys.argv[2])
            output_format = sys.argv[3] if len(sys.argv) > 3 else "JPEG"
            # This would call the conversion function directly
            console.print(
                f"[yellow]Converting {input_file} to {output_format}[/yellow]")
        elif command == "convert-video":
            if len(sys.argv) < 3:
                console.print("[red]Error: Input file required[/red]")
                return
            # Handle convert-video command
            input_file = Path(sys.argv[2])
            codec = sys.argv[3] if len(sys.argv) > 3 else "h264"
            quality = sys.argv[4] if len(sys.argv) > 4 else "high"
            # This would call the conversion function directly
            console.print(
                f"[yellow]Converting {input_file} to {codec} with {quality} quality[/yellow]")
        elif command == "batch-convert":
            if len(sys.argv) < 3:
                console.print("[red]Error: Directory required[/red]")
                return
            # Handle batch-convert command
            directory = Path(sys.argv[2])
            conv_type = sys.argv[3] if len(sys.argv) > 3 else "both"
            console.print(
                f"[yellow]Batch converting {directory} for {conv_type} files[/yellow]")
        elif command == "remove-aae":
            if len(sys.argv) < 3:
                console.print("[red]Error: Directory required[/red]")
                return
            # Handle remove-aae command
            directory = Path(sys.argv[2])
            console.print(
                f"[yellow]Removing AAE files from {directory}[/yellow]")
        elif command == "status":
            cli_manager.show_status_interactive()
        elif command == "logs":
            cli_manager.view_logs_interactive()
        elif command == "check-deps":
            cli_manager.check_dependencies_interactive()
        elif command == "hw-accel":
            cli_manager.check_hardware_accel_interactive()
        else:
            console.print(
                f"[yellow]Command '{command}' not recognized[/yellow]")
            cli_manager.show_menu()
    else:
        # Default to interactive mode
        cli_manager.show_interactive_menu()


if __name__ == "__main__":
    main()
