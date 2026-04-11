# Video Downloader Project: Moduláris Architektúra és Lépésről Lépésre Terv

Ez a dokumentum a RAG (Retrieval-Augmented Generation) tudásbázisából kinyert információk és a "Labor" (Gemini & User) koncepciói alapján meghatározza a robusztus, jövőálló és moduláris könyvtárszerkezetet, amely képes kezelni a legnehezebb, obfuszkált, bot-védelemmel (pl. Cloudflare) ellátott streameket, valamint a DRM-védett médiák detektálását is.

## 1. Rendszer Architektúra

A projekt négy, egymástól jól elszeparált, de együttműködő logikai szakaszra (modulra) bomlik:

*   **A. Sniffer (Hálózati Felderítő):** A `Playwright` és (szükség esetén) az `undetected-chromedriver` eszköztára. Ez a modul "láthatatlan" böngészőként viselkedik, lefuttatja a Cloudflare/Captchákat, lekezeli az iframe-eket (pl. `rpmshare`, `vidoza`), majd elkapja az `.m3u8` vagy `.mpd` (DASH) manifeszt URL-jét, és a hozzá tartozó hitelesítési adatokat (Cookie-k, Headerek). Ha Widevine (DRM) kérést vagy kódolt kulcsot (`#EXT-X-KEY`) észlel, megszakít/figyelmeztet.
*   **B. Core (Nyers Letöltő Motor):** A `yt-dlp` Python API-jára épülő letöltő egység. Semmilyen "kitaláló" logikát nem végez (az a Sniffer dolga); ő a Sniffer által készített `session_config.json` alapján hitelesíti magát a szerver felé, pontosan klónozva a Sniffer ujjlenyomatát (User-Agent). Ez az egység felel a több szálon futó, megszakadás-tűrő letöltésért.
*   **C. Post-Processor (Utómunka & Egyesítés):** A darabolt (`.m4s`, `.ts`) streamek, vagy különválasztott hang/kép sávok esetén hívja meg az `ffmpeg`-et, illetve ha a hálózat nagyon speciális (vagy DASH repackaging kell), akkor a `Bento4` / `shaka-packager` logikáját alkalmazza.
*   **D. UI (Felhasználói Felület):** A `Flet` alapú frontend. Egy elegáns, asztali sötét módú (dark-mode) felület, amely valós időben (progress-hookok segítségével) jeleníti meg a letöltési folyamatot, a hálózati Sniffer eseményeket és a hibákat.

## 2. Könyvtárszerkezet (Mappastruktúra)

A fenti logika alapján a projekt könyvtárszerkezete a következő (amelyet a jelenlegi commitban hozunk létre):

```text
/
├── .gitignore                   # Kiterjesztett gitignore (DB, Index, cache, session fájlok)
├── README.md                    # Általános projekt leírás
├── agents.md                    # Jules (az Agent) belső működési protokollja
├── PROJECT_ARCHITECTURE.md      # EZ A DOKUMENTUM: Az architekturális terv
│
├── src/                         # A Python kódok fő gyökere
│   ├── sniffer/                 # A "Hálózati Felderítő" (Phase 1)
│   │   ├── __init__.py
│   │   ├── sniffer_poc.py       # A Playwright-alapú manifeszt-elkapó szkript
│   │   └── stealth_utils.py     # (Későbbi) Bot-védelem elkerülését segítő logika
│   │
│   ├── core/                    # A "Nyers Letöltő" (Phase 2)
│   │   ├── __init__.py
│   │   └── downloader.py        # yt-dlp API integráció (Progress Hookokkal)
│   │
│   ├── processor/               # A "Műtő" (Phase 3)
│   │   ├── __init__.py
│   │   └── media_merger.py      # FFmpeg parancsok (TS, M4S, külön sávok összefűzése)
│   │
│   ├── ui/                      # Az "Irányítóterem" (Phase 4)
│   │   ├── __init__.py
│   │   └── flet_app.py          # A Flet grafikus felület belépési pontja
│   │
│   └── utils/                   # Globális segédprogramok
│       ├── __init__.py
│       ├── config_manager.py    # A session_config.json és egyéb configok olvasója
│       └── drm_detector.py      # Widevine/PlayReady PSSH és MPD analízis
│
├── RAG_SYSTEM/                  # A RAG tudásbázis építő és vallató szkriptjei (Kész)
│   ├── RAG_SETUP.md
│   ├── knowledge_builder.py
│   ├── rag_builder.py
│   ├── rag_interrogator.py
│   └── restore_env_vd.py
│
└── Hardver/                     # Elemzések a hardveres/architekturális korlátokról (Kész)
    ├── HARDVER_SPEC.md
    ├── REPO_ARCHITEKTURA_JAVASLAT.md
    └── repo_list.txt
```

## 3. Lépésről Lépésre Terv (Kivitelezési Menetrend)

1.  **FÁZIS: A Mappaszerkezet kialakítása (Jelenlegi Lépés)**
    *   *Állapot:* Az `src/` könyvtár és az almappák létrehozása, a meglévő `sniffer_poc.py` áthelyezése.

2.  **FÁZIS: A "Nyers Letöltő" (yt-dlp Core) implementálása**
    *   *Feladat:* Megírni a `src/core/downloader.py` fájlt.
    *   *RAG fókusz:* A `yt_dlp.YoutubeDL` Python API dokumentációjának kikeresése.
    *   *Logika:* Olvassa be a `src/sniffer/session_config.json`-t, importálja a `User-Agent`-et és a `Referer`-t a `http_headers` paraméterbe, valamint inicializálja a letöltést az elkapott `.m3u8`/`.mpd` linken. Célzott Progress Hook megírása.

3.  **FÁZIS: A Sniffer és a Core összekötése**
    *   *Feladat:* Egy automatizált vezérlő (Controller) megírása, amely meghívja a Sniffer-t, ellenőrzi a DRM-et (megszakít, ha Widevine-t lát), majd egyből átadja a folyamatot a Core-nak.

4.  **FÁZIS: FFmpeg Utófeldolgozás**
    *   *Feladat:* A `src/processor/media_merger.py` megírása.
    *   *RAG fókusz:* Hogyan kezeljük a `-c copy` veszteségmentes összefűzéseket, illetve hogyan javítsuk a korrupt fejlécű ts szegmenseket.

5.  **FÁZIS: Flet UI Építése és Tesztelés**
    *   *Feladat:* Az `src/ui/flet_app.py` elkészítése.
    *   *Logika:* Felület kialakítása (TextField, ProgressBar, LogTerminal), és az async/szálas hívások integrálása (hogy a letöltés ne fagyassza ki a UI-t).
    *   *Eseménykezelés:* Stabil hibaüzenetek (pl. lejárt süti, megszakadt hálózat) közvetítése a felhasználónak.