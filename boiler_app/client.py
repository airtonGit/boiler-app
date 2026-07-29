"""Cliente da API eWeLink para consulta de dispositivos."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from ewelink import EWeLink
from ewelink.types import AppCredentials, EmailUserCredentials


@dataclass
class BoilerInfo:
    """Informações de um boiler/termostato."""

    name: str
    device_id: str
    online: bool
    model: str
    current_temperature: Optional[float] = None
    current_humidity: Optional[str] = None
    switch: Optional[str] = None
    rssi: Optional[int] = None
    sensor_type: Optional[str] = None
    temp_correction: Optional[int] = None
    firmware_version: Optional[str] = None
    temp_unit: Optional[int] = None
    temp_range_min: Optional[float] = None
    temp_range_max: Optional[float] = None
    auto_control_enabled: bool = False
    auto_control_zones: list[dict] = field(default_factory=list)


def _parse_boiler(item_data: dict) -> BoilerInfo:
    """Converte dados brutos da API em BoilerInfo."""
    params = item_data.get("params", {})
    settings = item_data.get("settings", {})

    # Extrai ranges de temperatura
    temp_lower = params.get("updateListTempLower", [])
    temp_upper = params.get("updateListTempUpper", [])

    # Extrai zonas de auto-controle
    auto_zones = []
    for zone in params.get("autoControl", []):
        if zone.get("enable"):
            targets = zone.get("targets", [])
            eff_time = zone.get("effTime", {})
            high = None
            low = None
            for t in targets:
                if "high" in t:
                    high = float(t["high"])
                if "low" in t:
                    low = float(t["low"])
            auto_zones.append({
                "time": f"{eff_time.get('fromLocal', '?')} - {eff_time.get('toLocal', '?')}",
                "low": low,
                "high": high,
            })

    return BoilerInfo(
        name=item_data.get("name", "Desconhecido"),
        device_id=item_data.get("deviceid", ""),
        online=item_data.get("online", False),
        model=item_data.get("productModel", ""),
        current_temperature=(
            float(params["currentTemperature"])
            if params.get("currentTemperature") not in (None, "unavailable")
            else None
        ),
        current_humidity=params.get("currentHumidity"),
        switch=params.get("switch"),
        rssi=params.get("rssi"),
        sensor_type=params.get("sensorType"),
        temp_correction=params.get("tempCorrection"),
        firmware_version=params.get("fwVersion"),
        temp_unit=params.get("tempUnit"),
        temp_range_min=float(temp_lower[0]) if temp_lower else None,
        temp_range_max=float(temp_upper[0]) if temp_upper else None,
        auto_control_enabled=bool(params.get("autoControlEnabled")),
        auto_control_zones=auto_zones,
    )


class BoilerClient:
    """Cliente para consultar boilers via API eWeLink."""

    def __init__(
        self,
        email: str,
        password: str,
        country_code: str = "+55",
        region: str = "us",
        app_id: str = "4s1FXKC9FaGfoqXhmXSJneb3qcm1gOak",
        app_secret: str = "oKvCM06gvwkRbfetd6qWRrbC3rFrbIpV",
    ):
        self._app_cred = AppCredentials(id=app_id, secret=app_secret)
        self._user_cred = EmailUserCredentials(
            email=email,
            password=password,
            country_code=country_code,
        )
        self._region = region
        self._client: Optional[EWeLink] = None

    async def _get_client(self) -> EWeLink:
        if self._client is None:
            self._client = EWeLink(
                app_cred=self._app_cred,
                user_cred=self._user_cred,
            )
            await self._client.login(region=self._region)  # type: ignore[arg-type]
        return self._client

    async def get_boilers(self) -> list[BoilerInfo]:
        """Obtém a lista de boilers e seus status."""
        client = await self._get_client()

        # Usa a API diretamente para evitar problemas de parsing da lib
        import aiohttp

        login_resp = client._login
        if login_resp is None:
            await client.login(region=self._region)  # type: ignore[arg-type]
            login_resp = client._login

        domains = {
            "as": "https://as-apia.coolkit.cc",
            "cn": "https://cn-apia.coolkit.cn",
            "eu": "https://eu-apia.coolkit.cc",
            "us": "https://us-apia.coolkit.cc",
        }
        api_base = domains.get(self._region, domains["us"])

        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {login_resp.access_token}",
                "X-CK-Appid": self._app_cred.id,
            }
            async with session.get(
                f"{api_base}/v2/device/thing", headers=headers
            ) as resp:
                data = await resp.json()

        if data.get("error") != 0:
            raise RuntimeError(f"Erro na API: {data.get('msg', 'erro desconhecido')}")

        boilers = []
        for thing in data["data"]["thingList"]:
            item = thing["itemData"]
            boilers.append(_parse_boiler(item))

        return boilers

    async def close(self):
        if self._client:
            try:
                await self._client.logout()
            except Exception:
                pass
            try:
                await self._client._client_session.close()
            except Exception:
                pass
            self._client = None
