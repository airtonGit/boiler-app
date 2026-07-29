"""CLI do Boiler App - Monitor de temperatura de boilers eWeLink."""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

from .client import BoilerClient
from .report import render_report, render_summary


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

    args = parser.parse_args()

    # Carrega .env se existir
    load_dotenv()

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

    client = BoilerClient(
        email=email,
        password=password,
        country_code=country_code,
        region=region,
        app_id=app_id,
        app_secret=app_secret,
    )

    try:
        boilers = asyncio.run(client.get_boilers())

        if args.json:
            import json

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
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif args.summary:
            render_summary(boilers)
        else:
            render_report(boilers)

    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)
    finally:
        asyncio.run(client.close())


if __name__ == "__main__":
    main()
