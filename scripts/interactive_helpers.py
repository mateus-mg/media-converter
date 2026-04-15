#!/usr/bin/env python3
"""
Interactive prompt helpers for Media Converter.
Shared by CLI and main script.
"""

from typing import Callable, Dict, Optional

from rich.console import Console

InputFunc = Callable[[str], str]
PrintFunc = Callable[[str], None]

console = Console()

DEFAULT_CONFIG: Dict[str, object] = {
    'image_format': 'JPEG',
    'video_codec': 'h264',
    'video_quality': 'auto',
    'resize': 'none',
    'dry_run': False,
    'delete_originals': False,
    'remove_aae': False,
    'only_images': False,
    'only_videos': False,
}


def prompt_choice(
    question: str,
    choices: Dict[str, str],
    default_key: str,
    input_func: InputFunc = input,
    print_func: PrintFunc = print,
) -> str:
    """Prompt for a choice and return the selected key."""
    choice_keys = "/".join(sorted(choices.keys()))

    console.print(f"[bold]{question}:[/bold]")
    for key in sorted(choices.keys()):
        default_marker = " (default)" if key == default_key else ""
        console.print(f"  [cyan][{key}][/cyan] {choices[key]}{default_marker}")

    while True:
        prompt_plain = f"Your choice [{choice_keys}] ({default_key}): "
        prompt_rich = (
            f"[bold]Your choice[/bold] "
            f"[magenta][{choice_keys}][/magenta] "
            f"([cyan]{default_key}[/cyan]): "
        )

        # Use Rich prompt styling in normal CLI flow; keep plain input for custom input functions/tests.
        if input_func is input:
            response = console.input(prompt_rich).strip()
        else:
            response = input_func(prompt_plain).strip()
        if not response:
            response = default_key
        if response in choices:
            return response
        console.print(
            f"[red]Invalid choice.[/red] Choose one of: {', '.join(sorted(choices.keys()))}")


def prompt_yes_no(
    question: str,
    default: bool = False,
    input_func: InputFunc = input,
    print_func: PrintFunc = print,
) -> bool:
    """Prompt for yes/no and return True or False."""
    default_hint = "Y/n" if default else "y/N"
    while True:
        response = input_func(f"{question} ({default_hint}): ").strip().lower()
        if not response:
            return default
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        console.print("[red]Please answer with 'y' (yes) or 'n' (no).[/red]")


def build_conversion_config(
    preselected_mode: Optional[str] = None,
    input_func: InputFunc = input,
    print_func: PrintFunc = print,
) -> Dict[str, object]:
    """Build a conversion configuration through interactive prompts."""
    config: Dict[str, object] = dict(DEFAULT_CONFIG)

    if preselected_mode == "images":
        config['only_images'] = True
        config['only_videos'] = False
    elif preselected_mode == "videos":
        config['only_images'] = False
        config['only_videos'] = True
    elif preselected_mode is None:
        pass
    else:
        raise ValueError(
            "Invalid preselected_mode. Use 'images', 'videos', or None.")

    console.print("\n[bold cyan]Setup Options[/bold cyan]")
    customize = prompt_yes_no(
        "Customize conversion settings?",
        default=False,
        input_func=input_func,
        print_func=print_func,
    )

    if customize:
        console.print("\n[bold cyan]Conversion Settings[/bold cyan]")
        console.print("[bold]Select the desired options:[/bold]")

        if preselected_mode is None:
            console.print("\n[bold cyan][1] Processing Mode[/bold cyan]")
            processing_choice = prompt_choice(
                "Choose what to process",
                {"1": "All files (images and videos)",
                 "2": "Images only", "3": "Videos only"},
                "1",
                input_func=input_func,
                print_func=print_func,
            )
            if processing_choice == "2":
                config['only_images'] = True
            elif processing_choice == "3":
                config['only_videos'] = True

        if not config['only_videos']:
            console.print("\n[bold cyan][2] Image Format[/bold cyan]")
            img_choice = prompt_choice(
                "Choose output format for HEIC/HEIF",
                {"1": "JPEG (95% quality, smaller files)",
                 "2": "PNG (lossless, larger files)"},
                "1",
                input_func=input_func,
                print_func=print_func,
            )
            config['image_format'] = "PNG" if img_choice == "2" else "JPEG"

        if not config['only_images']:
            console.print("\n[bold cyan][3] Video Codec[/bold cyan]")
            vid_choice = prompt_choice(
                "Choose video codec",
                {
                    "1": "H.264 (maximum compatibility, universal)",
                    "2": "H.265 (best compression, smaller files)",
                    "3": "Copy (remux only, no re-encoding)"
                },
                "1",
                input_func=input_func,
                print_func=print_func,
            )
            if vid_choice == "2":
                config['video_codec'] = "h265"
            elif vid_choice == "3":
                config['video_codec'] = "copy"
            else:
                config['video_codec'] = "h264"

            console.print("\n[bold cyan][4] Video Quality[/bold cyan]")
            quality_choice = prompt_choice(
                "Choose compression level",
                {
                    "1": "Auto (recommended; adjusts by resolution)",
                    "2": "High (CRF 18, visually lossless)",
                    "3": "Medium (CRF 23, good quality, smaller)",
                    "4": "Lossless (very large files)"
                },
                "1",
                input_func=input_func,
                print_func=print_func,
            )
            if quality_choice == "2":
                config['video_quality'] = "high"
            elif quality_choice == "3":
                config['video_quality'] = "medium"
            elif quality_choice == "4":
                config['video_quality'] = "lossless"
            else:
                config['video_quality'] = "auto"

            console.print("\n[bold cyan][5] Video Resizing[/bold cyan]")
            resize_choice = prompt_choice(
                "Choose output resolution",
                {
                    "1": "None (keep original resolution)",
                    "2": "1080p (1920x1080)",
                    "3": "2K (2560x1440)",
                    "4": "4K (keep original, default)"
                },
                "1",
                input_func=input_func,
                print_func=print_func,
            )
            if resize_choice == "2":
                config['resize'] = "1080p"
            elif resize_choice == "3":
                config['resize'] = "2k"
            elif resize_choice == "4":
                config['resize'] = "4k"
            else:
                config['resize'] = "none"

        console.print("\n[bold cyan][6] Additional Options[/bold cyan]")
        config['dry_run'] = prompt_yes_no(
            "Dry run mode (test without processing)?",
            default=False,
            input_func=input_func,
            print_func=print_func,
        )

    # Mandatory questions always asked, regardless of customize option
    console.print("\n[bold cyan]Required Settings[/bold cyan]")
    config['delete_originals'] = prompt_yes_no(
        "Delete originals after successful conversion?",
        default=False,
        input_func=input_func,
        print_func=print_func,
    )

    # Ask about AAE removal only if processing images (not videos-only mode)
    if not config['only_videos']:
        config['remove_aae'] = prompt_yes_no(
            "Remove .AAE files (Apple metadata)?",
            default=False,
            input_func=input_func,
            print_func=print_func,
        )

    console.print("\n[bold green]Configuration completed.[/bold green]")
    return config
