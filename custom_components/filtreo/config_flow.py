"""Configurazione dalla schermata di Home Assistant.

Con l'add-on Filtreo (stesso apparecchio di Home Assistant) l'add-on lascia in collegamento.json la porta e la chiave:
basta un clic. Con Filtreo su un altro apparecchio (per esempio il Jetson) si scrivono indirizzo, porta e chiave
(il pannello di Filtreo, Impostazioni → «Home Assistant e HomeKit», li mostra).
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FiltreoChiaveErrata, FiltreoErrore, prova
from .const import CONF_TOKEN, DOMAIN, FILE_COLLEGAMENTO, HOST_CANDIDATI, PORTA_PREDEFINITA

_LOGGER = logging.getLogger(__name__)


def _leggi_collegamento(hass: HomeAssistant) -> dict[str, Any]:
    try:
        with open(hass.config.path(FILE_COLLEGAMENTO), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) and d.get("token") else {}
    except (OSError, ValueError):
        return {}


class FiltreoConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._auto: dict[str, Any] = {}
        self._trovato: dict[str, Any] = {}
        self._attesa: asyncio.Task | None = None
        self._esito: dict[str, Any] = {}

    async def _controlla(self, host: str, porta: int, token: str) -> tuple[dict[str, Any] | None, str | None]:
        try:
            dati = await prova(async_get_clientsession(self.hass), host, porta, token)
        except FiltreoChiaveErrata:
            return None, "invalid_auth"
        except FiltreoErrore:
            return None, "cannot_connect"
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Errore inatteso parlando con Filtreo")
            return None, "unknown"
        return dati, None

    async def _crea(self, host: str, porta: int, token: str, dati: dict[str, Any]) -> ConfigFlowResult:
        await self.async_set_unique_id(dati.get("nodo") or f"{host}:{porta}")
        self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: porta, CONF_TOKEN: token})
        return self.async_create_entry(title="Filtreo", data={CONF_HOST: host, CONF_PORT: porta, CONF_TOKEN: token})

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            # add-on sullo stesso apparecchio: provo gli indirizzi noti con la chiave lasciata dall'add-on
            coll = await self.hass.async_add_executor_job(_leggi_collegamento, self.hass)
            if coll:
                porta = int(coll.get("porta") or PORTA_PREDEFINITA)
                for host in HOST_CANDIDATI:
                    dati, err = await self._controlla(host, porta, coll["token"])
                    if dati is not None:
                        self._auto = {CONF_HOST: host, CONF_PORT: porta, CONF_TOKEN: coll["token"], "dati": dati}
                        return await self.async_step_conferma()
        errori: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            porta = int(user_input[CONF_PORT])
            dati, err = await self._controlla(host, porta, user_input[CONF_TOKEN].strip())
            if dati is not None:
                return await self._crea(host, porta, user_input[CONF_TOKEN].strip(), dati)
            errori["base"] = err or "unknown"
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=(user_input or {}).get(CONF_HOST, "")): str,
            vol.Required(CONF_PORT, default=(user_input or {}).get(CONF_PORT, PORTA_PREDEFINITA)): int,
            vol.Required(CONF_TOKEN): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errori)

    async def async_step_hassio(self, discovery_info: Any) -> ConfigFlowResult:
        """0.10.3 — l'app FiltreoCasa si annuncia al Supervisor: Filtreo compare tra i dispositivi rilevati."""
        coll = await self.hass.async_add_executor_job(_leggi_collegamento, self.hass)
        if not coll:
            return self.async_abort(reason="cannot_connect")
        porta = int(coll.get("porta") or PORTA_PREDEFINITA)
        if coll.get("nodo"):
            await self.async_set_unique_id(coll["nodo"])
            self._abort_if_unique_id_configured()
        for host in HOST_CANDIDATI:
            dati, err = await self._controlla(host, porta, coll["token"])
            if dati is not None:
                self._auto = {CONF_HOST: host, CONF_PORT: porta, CONF_TOKEN: coll["token"], "dati": dati}
                return await self.async_step_conferma()
        return self.async_abort(reason="cannot_connect")

    # ── 0.10.3: Filtreo trovato nella rete (Bonjour _filtreo._tcp) → richiesta → «Consenti» nel pannello di Filtreo ──
    async def async_step_zeroconf(self, discovery_info: Any) -> ConfigFlowResult:
        prop = dict(getattr(discovery_info, "properties", {}) or {})
        host = str(getattr(discovery_info, "host", "") or "")
        if not host or ":" in host:   # solo IPv4: la rete di casa
            return self.async_abort(reason="cannot_connect")
        porta = int(prop.get("ha") or PORTA_PREDEFINITA)
        nodo = str(prop.get("nodo") or "").strip()
        if not nodo:   # Filtreo prima della 0.10.3: niente integrazione automatica
            return self.async_abort(reason="cannot_connect")
        await self.async_set_unique_id(nodo)   # lo stesso identificativo che usa la voce creata (vedi _crea)
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})
        coll = await self.hass.async_add_executor_job(_leggi_collegamento, self.hass)
        if coll:   # l'app è dentro questo Home Assistant: la chiave c'è già
            p2 = int(coll.get("porta") or porta)
            dati, _ = await self._controlla(host, p2, coll["token"])
            if dati is not None:
                self._auto = {CONF_HOST: host, CONF_PORT: p2, CONF_TOKEN: coll["token"], "dati": dati}
                return await self.async_step_conferma()
        self._trovato = {CONF_HOST: host, CONF_PORT: porta, "nome": str(prop.get("nome") or "Filtreo")}
        self.context["title_placeholders"] = {"name": self._trovato["nome"]}
        return await self.async_step_trovato()

    async def async_step_trovato(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self.async_show_form(step_id="trovato", description_placeholders={"host": self._trovato[CONF_HOST]})
        return await self.async_step_consenso()

    async def _aspetta_consenso(self) -> None:
        s = async_get_clientsession(self.hass)
        h, porta = self._trovato[CONF_HOST], self._trovato[CONF_PORT]
        base = f"http://{h}:{porta}/ha/v1/collega"
        nome = (self.hass.config.location_name or "Home Assistant")[:30]
        try:
            async with asyncio.timeout(10):
                async with s.post(base, json={"nome": f"Home Assistant · {nome}"}) as r:
                    d = await r.json(content_type=None)
                    stato = r.status
            rid = d.get("id") if stato == 200 else None
            if not rid:
                self._esito = {"errore": "rifiutato" if stato == 403 else "cannot_connect"}
                return
            for _ in range(300):   # fino a 10 minuti
                await asyncio.sleep(2)
                try:
                    async with asyncio.timeout(8):
                        async with s.get(f"{base}/{rid}") as r2:
                            e = await r2.json(content_type=None)
                except Exception:  # noqa: BLE001
                    continue
                st = e.get("stato")
                if st == "consentito" and e.get("token"):
                    self._esito = {"token": e["token"]}
                    return
                if st in ("rifiutato", "scaduta"):
                    self._esito = {"errore": "rifiutato" if st == "rifiutato" else "scaduto"}
                    return
            self._esito = {"errore": "scaduto"}
        except Exception:  # noqa: BLE001
            self._esito = {"errore": "cannot_connect"}

    async def async_step_consenso(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._attesa is None:
            self._attesa = self.hass.async_create_task(self._aspetta_consenso())
        if not self._attesa.done():
            return self.async_show_progress(step_id="consenso", progress_action="consenso", progress_task=self._attesa)
        return self.async_show_progress_done(next_step_id="fine")

    async def async_step_fine(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if "token" not in self._esito:
            return self.async_abort(reason=self._esito.get("errore", "cannot_connect"))
        h, porta, tok = self._trovato[CONF_HOST], self._trovato[CONF_PORT], self._esito["token"]
        dati, err = await self._controlla(h, porta, tok)
        if dati is None:
            return self.async_abort(reason=err or "cannot_connect")
        return await self._crea(h, porta, tok, dati)

    async def async_step_conferma(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        a = self._auto
        if user_input is not None:
            return await self._crea(a[CONF_HOST], a[CONF_PORT], a[CONF_TOKEN], a["dati"])
        return self.async_show_form(step_id="conferma", description_placeholders={"host": a[CONF_HOST]})

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        voce = self._get_reauth_entry()
        errori: dict[str, str] = {}
        if user_input is not None:
            dati, err = await self._controlla(voce.data[CONF_HOST], voce.data[CONF_PORT], user_input[CONF_TOKEN].strip())
            if dati is not None:
                return self.async_update_reload_and_abort(voce, data_updates={CONF_TOKEN: user_input[CONF_TOKEN].strip()})
            errori["base"] = err or "unknown"
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
                                    errors=errori)
