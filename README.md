# Filtreo per Home Assistant

L'integrazione di **Filtreo**, il filtro anti pubblicità e tracker per tutta la casa: protezione, pausa e numero di richieste bloccate dentro Home Assistant, utilizzabili anche nelle automazioni.

Serve quando **FiltreoCasa** gira su un altro apparecchio di casa (per esempio un Jetson o un Raspberry) e Home Assistant non ha la Raccolta delle app. Con Home Assistant OS installa invece l'app FiltreoCasa da [filtreo-app/home-assistant](https://github.com/filtreo-app/home-assistant): l'integrazione arriva da sola.

## Installazione con HACS

1. **HACS** › menu ⋮ › **Archivi digitali personalizzati** › incolla `https://github.com/filtreo-app/integrazione-home-assistant`, tipo **Integrazione** › aggiungi.
2. Cerca **Filtreo** in HACS › **Scarica**.
3. Riavvia Home Assistant.
4. In **Impostazioni › Dispositivi e servizi** Filtreo compare tra i rilevati: premi **Configura**, poi **Invia**, poi **Consenti** nel pannello di Filtreo.
