#!/usr/bin/env python3
"""
Log Formatter - Hierarchical log formatter with 3 levels of structure

Provides structured logging output with:
    - Major headers (level 1): Section separators
    - Minor headers (level 2): Subsection titles
    - Items (level 3): Key-value pairs

Symbols (reduced usage):
    - ✓: Success
    - ✗: Error
    - !: Warning

Usage:
    from log_formatter import LogSection, format_conversion_session

    section = LogSection()
    print(section.major_header("CONVERSION START"))
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class LogSection:
    """Hierarchical log formatter with 3 levels of structure."""

    # Separadores visuais
    SEP_MAJOR = "━" * 80
    SEP_MINOR = "─" * 80

    # Indentação por nível
    INDENT_L1 = ""
    INDENT_L2 = "  "
    INDENT_L3 = "    "

    # Símbolos (uso reduzido)
    CHECK = "OK"
    CROSS = "X"
    ARROW = ">"
    BULLET = "-"

    @staticmethod
    def major_header(title: str, subtitle: str = None) -> List[str]:
        """
        Major section header (Level 1)

        Args:
            title: Main section title
            subtitle: Optional subtitle (additional info)

        Returns:
            List of formatted lines

        Example:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            CONVERSION STARTED - 2026-02-14 22:55:03
            PID: 3334771 | Session: a7f3c | Total Files: 127
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        lines = [LogSection.SEP_MAJOR, title]
        if subtitle:
            lines.append(subtitle)
        lines.append(LogSection.SEP_MAJOR)
        return lines

    @staticmethod
    def minor_header(title: str) -> List[str]:
        """
        Subsection header (Level 2)

        Args:
            title: Subsection title

        Returns:
            List of formatted lines

        Example:
            ──────────────────────────────────────────────────────────
            Image Conversion: photo.HEIC → photo.JPG | 2.3MB | 320kbps
            ──────────────────────────────────────────────────────────
        """
        return [LogSection.SEP_MINOR, title, LogSection.SEP_MINOR]

    @staticmethod
    def section(title: str, items: Dict[str, Any], indent: str = INDENT_L2) -> List[str]:
        """
        Section with multiple items (Level 2)

        Args:
            title: Section title
            items: Dictionary with key-value pairs
            indent: Indentation string (default: 2 spaces)

        Returns:
            List of formatted lines

        Example:
            Conversion Settings
              Format: HEIC to JPEG | Quality: 95% | Size: Original
              Hardware: Enabled | Preset: Balanced | Encoder: libx264
        """
        lines = [f"\n{title}"]

        for key, value in items.items():
            if isinstance(value, dict):
                # Sub-item (Nível 3)
                lines.append(f"{indent}{key}")
                for k, v in value.items():
                    lines.append(f"{indent}{indent}{k}: {v}")
            elif isinstance(value, list):
                # Lista de valores
                lines.append(f"{indent}{key}:")
                for item in value:
                    lines.append(f"{indent}{indent}{LogSection.BULLET} {item}")
            else:
                # Item simples
                lines.append(f"{indent}{key}: {value}")

        return lines

    @staticmethod
    def inline_section(title: str, items: Dict[str, Any], sep: str = " | ") -> str:
        """
        Compact inline section with separator

        Args:
            title: Inline section title
            items: Dictionary with key-value pairs
            sep: Separator between items (default: " | ")

        Returns:
            Inline formatted string

        Example:
            "Settings: Format: HEIC to JPEG | Quality: 95% | Size: Original"
        """
        items_str = sep.join([f"{k}: {v}" for k, v in items.items()])
        return f"{title}: {items_str}" if title else items_str

    @staticmethod
    def key_value_list(items: Dict[str, Any], sep: str = " | ", max_items: Optional[int] = None) -> str:
        """
        Inline-separated key-value list

        Args:
            items: Dictionary with key-value pairs
            sep: Separator between items (default: " | ")
            max_items: Maximum number of items (None = all)

        Returns:
            Inline formatted string

        Example:
            "Format: HEIC to JPEG | Quality: 95% | Size: Original"
        """
        items_list = list(items.items())
        if max_items:
            items_list = items_list[:max_items]

        return sep.join([f"{k}: {v}" for k, v in items_list])

    @staticmethod
    def progress_line(current: int, total: int, label: str = "Progress",
                      extras: Optional[Dict[str, Any]] = None) -> str:
        """
        Progress line with additional information

        Args:
            current: Current value
            total: Total value
            label: Progress label (default: "Progress")
            extras: Additional info to add

        Returns:
            Formatted string

        Example:
            "[Progress: 23/25 | 2 failed | 68 quota left | Elapsed: 4m 12s]"
        """
        percentage = (current / total * 100) if total > 0 else 0
        parts = [f"{current}/{total} ({percentage:.1f}%)"]

        if extras:
            parts.extend([f"{k}: {v}" for k, v in extras.items()])

        return f"[{label}: {' | '.join(parts)}]"

    @staticmethod
    def conversion_item(input_file: str, output_file: str, details: Optional[str] = None,
                        status: str = "OK", indent: str = INDENT_L2) -> List[str]:
        """
        Structured conversion item

        Args:
            input_file: Input file
            output_file: Output file
            details: Conversion details (size, quality, codec)
            status: Status symbol (default: "OK")
            indent: Indentation (default: 2 spaces)

        Returns:
            List of formatted lines

        Example:
            > photo.HEIC > photo.JPG
              Converted: 2.3MB | Quality: 95% | Time: 1.2s
        """
        lines = [f"{LogSection.ARROW} {input_file} → {output_file}"]
        if details:
            lines.append(f"{indent}{details}")
        return lines

    @staticmethod
    def error_block(title: str, details: Dict[str, Any]) -> List[str]:
        """
        Structured error block

        Args:
            title: Error title
            details: Error details (status, action, etc.)

        Returns:
            List of formatted lines

        Example:
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ERROR: CONVERSION FAILED
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            File: photo.HEIC
            Error: Unsupported format
            Action: Skipping file
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        lines = [LogSection.SEP_MAJOR, title, LogSection.SEP_MAJOR]
        for key, value in details.items():
            lines.append(f"{key}: {value}")
        lines.append(LogSection.SEP_MAJOR)
        return lines

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human-readable hours/minutes

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "4h 33m", "45m", "2h 00m")
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes:02d}m {seconds:02d}s"
        elif minutes > 0:
            return f"{minutes}m {seconds:02d}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def format_size(bytes_size: float) -> str:
        """
        Format file size in human-readable format

        Args:
            bytes_size: Size in bytes

        Returns:
            Formatted string (e.g., "8.3MB", "1.2GB")
        """
        if bytes_size >= 1024**3:
            return f"{bytes_size / (1024**3):.1f}GB"
        elif bytes_size >= 1024**2:
            return f"{bytes_size / (1024**2):.1f}MB"
        elif bytes_size >= 1024:
            return f"{bytes_size / 1024:.1f}KB"
        else:
            return f"{bytes_size:.0f}B"

    @staticmethod
    def format_timestamp(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Format timestamp in human-readable format

        Args:
            dt: datetime object (None = now)
            fmt: Output format

        Returns:
            Formatted string
        """
        if dt is None:
            dt = datetime.now()
        return dt.strftime(fmt)

    @staticmethod
    def table_row(columns: List[Any], widths: Optional[List[int]] = None, align: str = "left") -> str:
        """
        Format table row with aligned columns

        Args:
            columns: List of column values
            widths: List of widths for each column (None = auto)
            align: Alignment ("left", "right", "center")

        Returns:
            Formatted string

        Example:
            "Images: 70 converted | 18 failed | 30 remaining"
        """
        if widths is None:
            widths = [len(str(col)) for col in columns]

        formatted_cols = []
        for col, width in zip(columns, widths):
            col_str = str(col)
            if align == "right":
                formatted_cols.append(col_str.rjust(width))
            elif align == "center":
                formatted_cols.append(col_str.center(width))
            else:
                formatted_cols.append(col_str.ljust(width))

        return " ".join(formatted_cols)

    @staticmethod
    def summary_line(label: str, items: Dict[str, Any], sep: str = " | ") -> str:
        """
        Summary line with label and items

        Args:
            label: Line label (will be left-aligned)
            items: Dictionary of items
            sep: Separator between items

        Returns:
            Formatted string

        Example:
            "Results:  70 converted | 18 failed | 30 remaining"
        """
        label_formatted = f"{label}:".ljust(12)
        items_str = sep.join([f"{v} {k}" for k, v in items.items()])
        return f"{label_formatted}{items_str}"


class LogBuilder:
    """Builder for constructing complex logs fluently"""

    def __init__(self):
        self.lines: List[str] = []

    def add_major_header(self, title: str, subtitle: str = None) -> 'LogBuilder':
        """Add major header"""
        self.lines.extend(LogSection.major_header(title, subtitle))
        return self

    def add_minor_header(self, title: str) -> 'LogBuilder':
        """Add subsection header"""
        self.lines.extend(LogSection.minor_header(title))
        return self

    def add_section(self, title: str, items: Dict[str, Any], indent: str = LogSection.INDENT_L2) -> 'LogBuilder':
        """Add section with items"""
        self.lines.extend(LogSection.section(title, items, indent))
        return self

    def add_line(self, line: str) -> 'LogBuilder':
        """Add custom line"""
        self.lines.append(line)
        return self

    def add_blank(self, count: int = 1) -> 'LogBuilder':
        """Add blank lines"""
        self.lines.extend([""] * count)
        return self

    def build(self) -> List[str]:
        """Return list of constructed lines"""
        return self.lines

    def build_str(self, sep: str = "\n") -> str:
        """Return single string with all lines"""
        return sep.join(self.lines)


# Convenience functions for common cases
def format_conversion_session(start_time: datetime, total_files: int,
                            settings: Dict[str, Any], performance: Dict[str, Any],
                            checks: Dict[str, bool]) -> List[str]:
    """
    Format conversion session log

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    # Header
    builder.add_major_header(
        f"CONVERSION SESSION STARTED - {LogSection.format_timestamp(start_time)}",
        f"Files: {total_files} | Started: {start_time.strftime('%H:%M:%S')}"
    )

    # Settings section
    builder.add_section("Conversion Settings", settings)

    # Performance section
    builder.add_section("Performance", performance)

    # System checks
    check_items = {
        k: LogSection.CHECK if v else LogSection.CROSS for k, v in checks.items()}
    builder.add_section("System Checks", check_items)

    builder.add_line(LogSection.SEP_MAJOR)

    return builder.build()


def format_conversion_start(filename: str, file_info: Dict[str, Any],
                          settings: Dict[str, Any], processing: Dict[str, Any]) -> List[str]:
    """
    Format individual conversion start log

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    builder.add_minor_header(
        f"CONVERTING: {filename}"
    )

    # File info
    builder.add_line(LogSection.inline_section("File Info", file_info))

    # Settings
    builder.add_line(LogSection.inline_section("Settings", settings))

    # Processing info
    builder.add_line(LogSection.inline_section("Processing", processing))

    return builder.build()


def format_conversion_complete(filename: str, duration: float, results: Dict[str, Any],
                             quality: Dict[str, Any], errors: Dict[str, Any],
                             next_action: Optional[str] = None) -> List[str]:
    """
    Format conversion complete log

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    builder.add_minor_header(
        f"COMPLETED: {filename} - Duration: {LogSection.format_duration(duration)} ({duration:.2f}s)"
    )

    # Summary lines
    builder.add_line(LogSection.summary_line("Results", results))
    builder.add_line(LogSection.summary_line("Quality", quality))
    builder.add_line(LogSection.summary_line("Errors", errors))

    if next_action:
        builder.add_blank()
        builder.add_line(f"Next: {next_action}")

    return builder.build()


def format_batch_summary(total_processed: int, successful: int, failed: int,
                        total_size: float, elapsed_time: float,
                        throughput: float) -> List[str]:
    """
    Format batch conversion summary

    Args:
        total_processed: Total files processed
        successful: Successful files
        failed: Failed files
        total_size: Total size processed in bytes
        elapsed_time: Elapsed time in seconds
        throughput: Processing rate (files per second)

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    builder.add_major_header("BATCH CONVERSION SUMMARY")

    # Summary statistics
    stats = {
        "Processed": total_processed,
        "Successful": successful,
        "Failed": failed,
        "Success Rate": f"{(successful/total_processed*100):.1f}%" if total_processed > 0 else "0%"
    }
    builder.add_line(LogSection.inline_section("Statistics", stats))

    # Size and performance
    perf_stats = {
        "Total Size": LogSection.format_size(total_size),
        "Elapsed Time": LogSection.format_duration(elapsed_time),
        "Throughput": f"{throughput:.2f} files/sec"
    }
    builder.add_line(LogSection.inline_section("Performance", perf_stats))

    builder.add_line(LogSection.SEP_MAJOR)

    return builder.build()


def format_system_shutdown(summary: Dict[str, str]) -> List[str]:
    """
    Format system shutdown log

    Args:
        summary: Dictionary with formatted statistics

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    builder.add_major_header("MEDIA CONVERTER SHUTDOWN")

    builder.add_line("Final Statistics")
    for key, value in summary.items():
        builder.add_line(f"{LogSection.INDENT_L2}{LogSection.BULLET} {value}")

    builder.add_line(LogSection.SEP_MAJOR)

    return builder.build()


def format_hardware_detection(hw_accel: str, capabilities: Dict[str, Any]) -> List[str]:
    """
    Format hardware acceleration detection log

    Args:
        hw_accel: Detected acceleration type (qsv, nvenc, vaapi, none)
        capabilities: Acceleration capabilities

    Returns:
        List of formatted lines
    """
    builder = LogBuilder()

    title = f"HARDWARE ACCELERATION: {hw_accel.upper() if hw_accel != 'none' else 'NONE'}"
    if hw_accel != 'none':
        title += " (DETECTED AND ENABLED)"
    else:
        title += " (USING SOFTWARE ENCODING)"

    builder.add_minor_header(title)

    if capabilities:
        builder.add_section("Capabilities", capabilities)

    return builder.build()