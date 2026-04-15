#!/usr/bin/env python3
"""
Log Formatter - Estrutura hierárquica padronizada para logs
Media Converter System
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


class LogSection:
    """Formatador hierárquico de logs com 3 níveis de estrutura"""

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
        Cabeçalho de seção principal (Nível 1)

        Args:
            title: Título principal da seção
            subtitle: Subtítulo opcional (informações adicionais)

        Returns:
            Lista de linhas formatadas

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
        Cabeçalho de subseção (Nível 2)

        Args:
            title: Título da subseção

        Returns:
            Lista de linhas formatadas

        Example:
            ──────────────────────────────────────────────────────────
            Image Conversion: photo.HEIC → photo.JPG | 2.3MB | 320kbps
            ──────────────────────────────────────────────────────────
        """
        return [LogSection.SEP_MINOR, title, LogSection.SEP_MINOR]

    @staticmethod
    def section(title: str, items: Dict[str, Any], indent: str = INDENT_L2) -> List[str]:
        """
        Seção com múltiplos items (Nível 2)

        Args:
            title: Título da seção
            items: Dicionário com pares chave-valor
            indent: String de indentação (padrão: 2 espaços)

        Returns:
            Lista de linhas formatadas

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
        Seção compacta inline com separador

        Args:
            title: Título da seção inline
            items: Dicionário com pares chave-valor
            sep: Separador entre items (padrão: " | ")

        Returns:
            String formatada inline

        Example:
            "Settings: Format: HEIC to JPEG | Quality: 95% | Size: Original"
        """
        items_str = sep.join([f"{k}: {v}" for k, v in items.items()])
        return f"{title}: {items_str}" if title else items_str

    @staticmethod
    def key_value_list(items: Dict[str, Any], sep: str = " | ", max_items: Optional[int] = None) -> str:
        """
        Lista de pares chave-valor separados inline

        Args:
            items: Dicionário com pares chave-valor
            sep: Separador entre items (padrão: " | ")
            max_items: Número máximo de items (None = todos)

        Returns:
            String formatada inline

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
        Linha de progresso com informações adicionais

        Args:
            current: Valor atual
            total: Valor total
            label: Label do progresso (padrão: "Progress")
            extras: Informações extras para adicionar

        Returns:
            String formatada

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
        Item de conversão estruturado

        Args:
            input_file: Arquivo de entrada
            output_file: Arquivo de saída
            details: Detalhes da conversão (tamanho, qualidade, codec)
            status: Símbolo de status (padrão: "OK")
            indent: Indentação (padrão: 2 espaços)

        Returns:
            Lista de linhas formatadas

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
        Bloco de erro estruturado

        Args:
            title: Título do erro
            details: Detalhes do erro (status, action, etc.)

        Returns:
            Lista de linhas formatadas

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
        Formata duração em horas/minutos legível

        Args:
            seconds: Duração em segundos

        Returns:
            String formatada (ex: "4h 33m", "45m", "2h 00m")
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
        Formata tamanho de arquivo em formato legível

        Args:
            bytes_size: Tamanho em bytes

        Returns:
            String formatada (ex: "8.3MB", "1.2GB")
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
        Formata timestamp para formato legível

        Args:
            dt: Objeto datetime (None = agora)
            fmt: Formato de saída

        Returns:
            String formatada
        """
        if dt is None:
            dt = datetime.now()
        return dt.strftime(fmt)

    @staticmethod
    def table_row(columns: List[Any], widths: Optional[List[int]] = None, align: str = "left") -> str:
        """
        Formata linha de tabela com colunas alinhadas

        Args:
            columns: Lista de valores das colunas
            widths: Lista de larguras de cada coluna (None = auto)
            align: Alinhamento ("left", "right", "center")

        Returns:
            String formatada

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
        Linha de sumário com label e items

        Args:
            label: Label da linha (será alinhado à esquerda)
            items: Dicionário de items
            sep: Separador entre items

        Returns:
            String formatada

        Example:
            "Results:  70 converted | 18 failed | 30 remaining"
        """
        label_formatted = f"{label}:".ljust(12)
        items_str = sep.join([f"{v} {k}" for k, v in items.items()])
        return f"{label_formatted}{items_str}"


class LogBuilder:
    """Builder para construir logs complexos de forma fluente"""

    def __init__(self):
        self.lines: List[str] = []

    def add_major_header(self, title: str, subtitle: str = None) -> 'LogBuilder':
        """Adiciona cabeçalho principal"""
        self.lines.extend(LogSection.major_header(title, subtitle))
        return self

    def add_minor_header(self, title: str) -> 'LogBuilder':
        """Adiciona cabeçalho de subseção"""
        self.lines.extend(LogSection.minor_header(title))
        return self

    def add_section(self, title: str, items: Dict[str, Any], indent: str = LogSection.INDENT_L2) -> 'LogBuilder':
        """Adiciona seção com items"""
        self.lines.extend(LogSection.section(title, items, indent))
        return self

    def add_line(self, line: str) -> 'LogBuilder':
        """Adiciona linha customizada"""
        self.lines.append(line)
        return self

    def add_blank(self, count: int = 1) -> 'LogBuilder':
        """Adiciona linhas em branco"""
        self.lines.extend([""] * count)
        return self

    def build(self) -> List[str]:
        """Retorna lista de linhas construídas"""
        return self.lines

    def build_str(self, sep: str = "\n") -> str:
        """Retorna string única com todas as linhas"""
        return sep.join(self.lines)


# Funções de conveniência para casos comuns
def format_conversion_session(start_time: datetime, total_files: int,
                            settings: Dict[str, Any], performance: Dict[str, Any],
                            checks: Dict[str, bool]) -> List[str]:
    """
    Formata log de sessão de conversão

    Returns:
        Lista de linhas formatadas
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
    Formata log de início de conversão individual

    Returns:
        Lista de linhas formatadas
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
    Formata log de conclusão de conversão

    Returns:
        Lista de linhas formatadas
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
    Formata sumário de lote de conversões

    Args:
        total_processed: Total de arquivos processados
        successful: Arquivos com sucesso
        failed: Arquivos com falha
        total_size: Tamanho total processado em bytes
        elapsed_time: Tempo decorrido em segundos
        throughput: Taxa de processamento (arquivos por segundo)

    Returns:
        Lista de linhas formatadas
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
    Formata log de encerramento do sistema

    Args:
        summary: Dicionário com estatísticas formatadas

    Returns:
        Lista de linhas formatadas
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
    Formata log de detecção de aceleração de hardware

    Args:
        hw_accel: Tipo de aceleração detectada (qsv, nvenc, vaapi, none)
        capabilities: Capacidades de aceleração

    Returns:
        Lista de linhas formatadas
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