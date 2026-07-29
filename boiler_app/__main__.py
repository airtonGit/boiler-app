"""CLI do Boiler App - Monitor de temperatura de boilers eWeLink."""

import argparse
import asyncio
import os
import signal
import sys
import time

from dotenv import load_dotenv

from .client import BoilerClient
from .report import render_report, render_summary


def _build_client(args) -> BoilerClient:
    email = args.email or os.getenv("EWELINK_EMAIL")
    password = args.password or os.getenv("EWELINK_PASSWORD")
    country_code = args.country_code or os.getenv("EWELINK_COUNTRY_CODE", "+55")
    region = args.region or os.getenv("EWELINK_REGION", "us")
    app_id = args.app_id or os.getenv("EWELINK_APP_ID", "4s1FXKC9FaGfoqXhmXSJneb3qcm1gOak")
    app_secret = args.app_secret or os.getenv(
        "EWELINK_APP_SECRET", "oKvCM06gvwkRbfetd6qWRrbC3rFrbIpV"
    )

    if not email or not password:
        print("❌ Erro: Email e senha são obrigatórios.")
        print("   Defina via --email/--password ou crie um arquivo .env")
        print("   Veja .env.example para referência.")
        sys.exit(1)

    return BoilerClient(
        email=email,
        password=password,
        country_code=country_code,
        region=region,
        app_id=app_id,
        app_secret=app_secret,
    )


def _serialize(boilers):
    data = []
    for b in boilers:
        data.append({
            "name": b.name,
            "device_id": b.device_id,
            "online": b.online,
            "model": b.model,
            "current_temperature": b.current_temperature,
            "current_humidity": b.current_humidity,
            "switch": b.switch,
            "rssi": b.rssi,
            "sensor_type": b.sensor_type,
            "temp_correction": b.temp_correction,
            "firmware_version": b.firmware_version,
            "temp_unit": b.temp_unit,
            "temp_range_min": b.temp_range_min,
            "temp_range_max": b.temp_range_max,
            "auto_control_enabled": b.auto_control_enabled,
            "auto_control_zones": b.auto_control_zones,
        })
    return data


async def _watch_loop(client: BoilerClient, args):
    """Loop contínuo de monitoramento até Ctrl+C."""
    from rich.live import Live
    from rich.console import Console
    from rich.text import Text
    from datetime import datetime

    interval = args.interval
    console = Console()
    running = True
    first_run = True

    def _signal_handler(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    console.print("[cyan]🔍 Monitorando... Pressione Ctrl+C para sair.[/cyan]")
    console.print(f"[dim]   Atualizando a cada {interval}s[/dim]\n")

    while running:
        try:
            boilers = await client.get_boilers()

            if args.json:
                import json
                print(json.dumps(_serialize(boilers), indent=2, ensure_ascii=False))
            elif args.summary:
                render_summary(boilers, console)
            else:
                if not first_run:
                    # Limpa a tela para redesenhar (ANSI clear + move cursor home)
                    # Conta quantas linhas o último relatório ocupou e sobe
                    pass
                render_report(boilers, console)

            first_run = False

            # Aguarda o intervalo, mas verifica Ctrl+C a cada 1s
            for _ in range(interval):
                if not running:
                    break
                await asyncio.sleep(1)

        except Exception as e:
            console.print(f"[red]❌ Erro: {e}[/red]")
            # Espera antes de tentar de novo
            for _ in range(interval):
                if not running:
                    break
                await asyncio.sleep(1)

    console.print("\n[dim]👋 Monitoramento encerrado.[/dim]")


def main():
    parser = argparse.ArgumentParser(
        prog="boiler",
        description="🌡️  Monitor de temperatura de boilers eWeLink",
    )
    parser.add_argument(
        "--email",
        help="Email da conta eWeLink",
        default=None,
    )
    parser.add_argument(
        "--password",
        help="Senha da conta eWeLink",
        default=None,
    )
    parser.add_argument(
        "--country-code",
        default="+55",
        help="Código do país (default: +55)",
    )
    parser.add_argument(
        "--region",
        default="us",
        choices=["us", "eu", "cn", "as"],
        help="Região da API (default: us)",
    )
    parser.add_argument(
        "--app-id",
        default="4s1FXKC9FaGfoqXhmXSJneb3qcm1gOak",
        help="App ID do eWeLink",
    )
    parser.add_argument(
        "--app-secret",
        default="oKvCM06gvwkRbfetd6qWRrbC3rFrbIpV",
        help="App Secret do eWeLink",
    )
    parser.add_argument(
        "--summary",
        "-s",
        action="store_true",
        help="Mostra apenas resumo compacto",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Saída em formato JSON",
    )
    parser.add_argument(
        "--watch",
        "-w",
        action="store_true",
        help="Monitoramento contínuo (atualiza até Ctrl+C)",
    )
    parser.add_argument(
        "--interval",
        "-i",
        type=int,
        default=30,
        help="Intervalo entre atualizações em segundos (default: 30s)",
    )

    args = parser.parse_args()

    # Carrega .env se existir
    load_dotenv()

    client = _build_client(args)

    try:
        if args.watch:
            asyncio.run(_watch_loop(client, args))
        else:
            boilers = asyncio.run(client.get_boilers())

            if args.json:
                import json
                print(json.dumps(_serialize(boilers), indent=2, ensure_ascii=False))
            elif args.summary:
                render_summary(boilers)
            else:
                render_report(boilers)

    except KeyboardInterrupt:
        print("\n👋 Encerrado.")
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
    finally:
        asyncio.run(client.close())


if __name__ == "__main__":
    main()
