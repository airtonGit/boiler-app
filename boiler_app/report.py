"""Formatação de relatórios para o Boiler App."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from .client import BoilerInfo


def _temp_str(temp: Optional[float], unit: Optional[int] = None) -> str:
    """Formata temperatura com unidade."""
    if temp is None:
        return "[dim]N/A[/dim]"
    symbol = "°F" if unit == 1 else "°C"
    color = _temp_color(temp, unit)
    return f"[{color}]{temp:.1f}{symbol}[/{color}]"


def _temp_color(temp: float, unit: Optional[int] = None) -> str:
    """Retorna cor baseada na temperatura."""
    c = (temp - 32) * 5 / 9 if unit == 1 else temp
    if c < 20:
        return "cyan"
    elif c < 30:
        return "green"
    elif c < 45:
        return "yellow"
    elif c < 60:
        return "orange1"
    else:
        return "red"


def _rssi_bars(rssi: Optional[int]) -> str:
    """Mostra qualidade do sinal WiFi."""
    if rssi is None:
        return "[dim]N/A[/dim]"
    if rssi > -50:
        return "[green]▂▄▆█[/green]"
    elif rssi > -70:
        return "[yellow]▂▄▆ [/yellow]"
    elif rssi > -85:
        return "[orange1]▂▄  [/orange1]"
    else:
        return "[red]▂   [/red]"


def render_report(boilers: list[BoilerInfo], console: Optional[Console] = None) -> None:
    """Renderiza o relatório completo de boilers."""
    if console is None:
        console = Console()

    # Cabeçalho
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    console.print()
    console.print(
        Panel(
            Text(f"🌡️  Boiler Monitor  •  {now}", style="bold white"),
            box=box.HEAVY,
            border_style="cyan",
        )
    )

    if not boilers:
        console.print("[yellow]Nenhum boiler encontrado na conta.[/yellow]")
        return

    for boiler in boilers:
        _render_boiler_card(boiler, console)

    # Resumo
    online_count = sum(1 for b in boilers if b.online)
    console.print(
        f"[dim]Total: {len(boilers)} dispositivo(s)  •  "
        f"[green]{online_count} online[/green]  •  "
        f"[red]{len(boilers) - online_count} offline[/red][/dim]"
    )
    console.print()


def _render_boiler_card(boiler: BoilerInfo, console: Console) -> None:
    """Renderiza card individual de um boiler."""
    # Status
    status_icon = "🟢" if boiler.online else "🔴"
    switch_icon = "⚡ ON" if boiler.switch == "on" else "⏻ OFF"
    switch_color = "green" if boiler.switch == "on" else "dim"

    # Título
    title = Text()
    title.append(f"{status_icon}  ", style="")
    title.append(boiler.name, style="bold white")
    title.append(f"  [{switch_color}]{switch_icon}[/{switch_color}]", style="")

    # Tabela de detalhes
    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        show_header=False,
        padding=(0, 3),
    )
    table.add_column("Key", style="dim", width=14)
    table.add_column("Value", style="white")

    table.add_row("🌡️  Temperatura", _temp_str(boiler.current_temperature, boiler.temp_unit))

    if boiler.temp_range_min is not None and boiler.temp_range_max is not None:
        table.add_row(
            "📏 Range",
            f"{_temp_str(boiler.temp_range_min, boiler.temp_unit)} — "
            f"{_temp_str(boiler.temp_range_max, boiler.temp_unit)}",
        )

    table.add_row(
        "📶 Sinal WiFi",
        f"{_rssi_bars(boiler.rssi)} [dim]({boiler.rssi} dBm)[/dim]"
        if boiler.rssi is not None
        else "[dim]N/A[/dim]",
    )
    table.add_row("🔧 Sensor", boiler.sensor_type or "[dim]N/A[/dim]")

    if boiler.temp_correction:
        table.add_row("🔧 Corr. Temp.", f"{boiler.temp_correction:+d}°C")

    if boiler.auto_control_enabled and boiler.auto_control_zones:
        zones_text = Text()
        for i, zone in enumerate(boiler.auto_control_zones):
            prefix = "├─ " if i < len(boiler.auto_control_zones) - 1 else "└─ "
            zones_text.append(
                f"{prefix}{zone['time']}:  "
                f"[yellow]{zone['low']}°[/yellow] → "
                f"[red]{zone['high']}°[/red]",
                style="",
            )
            if i < len(boiler.auto_control_zones) - 1:
                zones_text.append("\n")
        table.add_row("⏰ Auto-Controle", zones_text)

    console.print(Panel(table, title=title, title_align="left", border_style="cyan"))
    console.print()


def render_summary(boilers: list[BoilerInfo], console: Optional[Console] = None) -> None:
    """Renderiza apenas um resumo compacto."""
    if console is None:
        console = Console()

    now = datetime.now().strftime("%H:%M:%S")
    console.print(f"[dim]{now}[/dim] ", end="")
    for b in boilers:
        if b.online:
            if b.current_temperature is not None:
                temp = _temp_str(b.current_temperature, b.temp_unit)
            else:
                temp = "[dim]?[/dim]"
            switch = "[green]ON[/green]" if b.switch == "on" else "[dim]OFF[/dim]"
            console.print(f"  {b.name}: {temp} {switch}")
        else:
            console.print(f"  {b.name}: [red]offline[/red]")
    console.print()
