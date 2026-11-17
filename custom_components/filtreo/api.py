"""Client HTTP verso la porta per Home Assistant di Filtreo (ha_integrazione.py)."""
from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class FiltreoErrore(Exception):
    """Filtreo non risponde."""


class FiltreoChiaveErrata(FiltreoErrore):
    """La chiave non è quella giusta."""


class FiltreoApi:
    def __init__(self, sessione: aiohttp.ClientSession, host: str, porta: int, token: str) -> None:
        self._s = sessione
        self.base = f"http://{host}:{porta}/ha/v1"
        self._h = {"Authorization": f"Bearer {token}"}

    async def _chiedi(self, metodo: str, percorso: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with asyncio.timeout(10):
                async with self._s.request(metodo, self.base + percorso, headers=self._h, params=params) as r:
                    if r.status == 401:
                        raise FiltreoChiaveErrata
                    dati = await r.json(content_type=None)
                    if r.status >= 500:
                        raise FiltreoErrore(str(dati)[:120])
                    return dati
        except FiltreoErrore:
            raise
        except (TimeoutError, aiohttp.ClientError, ValueError) as e:
            raise FiltreoErrore(str(e)) from e

    async def stato(self) -> dict[str, Any]:
        return await self._chiedi("GET", "/stato")

    async def pausa(self, minuti: int) -> dict[str, Any]:
        return await self._chiedi("POST", "/pausa", {"min": int(minuti)})

    async def spegni(self) -> dict[str, Any]:
        return await self._chiedi("POST", "/spegni")

    async def riprendi(self) -> dict[str, Any]:
        return await self._chiedi("POST", "/riprendi")

    async def modo(self, dispositivo: str, modalita: str) -> dict[str, Any]:
        return await self._chiedi("POST", "/modo", {"id": dispositivo, "m": modalita})


async def prova(sessione: aiohttp.ClientSession, host: str, porta: int, token: str) -> dict[str, Any]:
    """prova host/porta/chiave: ritorna lo stato oppure alza FiltreoErrore / FiltreoChiaveErrata"""
    return await FiltreoApi(sessione, host, porta, token).stato()
