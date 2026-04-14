# A Core Letöltő (Downloader) Kifejlesztésének Terve és Architektúrája

A `Video Downloader` projekt szíve a "Core" (letöltő) fázis. A projektünkben elvárás, hogy ne csak egy parancssori eszközt hívjunk meg (mint sok alapszintű alkalmazás), hanem a RAG-ban lévő, kiforrott nyílt forráskódú *download managerek* logikájának (a transzplantációs stratégiának) megfelelően, professzionális, aszinkron, Python-natív integrációt hozzunk létre.

## 1. Az Architektúra Felépítése

### A Hibrid Letöltő Motor (A `yt_dlp.YoutubeDL` API használata)
Célunk a `yt-dlp` beágyazása Python szintről (`yt_dlp.YoutubeDL(params)` használatával), mert így elkerülhető a subprocess I/O parsing nehézkessége, és sokkal közvetlenebb kommunikációt (event hooks) tesz lehetővé a grafikus felület (`Flet`) felé.

**Fő komponensek a `src/core` modulban:**
1.  **`downloader.py`**: Ez tartalmazza magát a letöltési osztályt (`VideoDownloader`). A feladata kizárólag egyetlen stream lekezelése a neki átadott paraméterek alapján.
2.  **`queue_manager/` (Új mappánk)**: A Queue (letöltési sor) felelős a párhuzamosításért. Szálkezeléssel (`concurrent.futures` vagy `asyncio` taskok) felügyeli, hogy hány letöltés futhat egyszerre anélkül, hogy a gép vagy a hálózat összeomlana.
3.  **Session Injector**: Képes beolvasni a `src/sniffer/session_config.json`-t (amit a Playwright generált) és beinjektálni a `http_headers`, `cookies` és `referer` mezőket a `yt-dlp` konfigurációjába (így játszva ki a Cloudflare-t vagy az IP-védelmet).

## 2. A Progress-Hook és Eseménykezelés (Event Emitter)

A meglévő nyílt forráskódú letöltőkből kinyert tudásanyag (pl. ezytdl, GDownloader) alapján a legfontosabb kihívás a UI fagyásmentes frissítése.

A letöltő architektúránk tartalmazni fog egy **Event Callback Mechanizmust**:
- A `yt-dlp` a `_hook_progress` metóduson keresztül (az `add_progress_hook`-ba regisztrált funkcióba) dictionary-ket dob (pl. `{'status': 'downloading', 'downloaded_bytes': 1000, ...}`).
- A `downloader.py` ezt a dictionary-t átalakítja egy szabványos "Event" objektummá, majd aszinkron módon egy callback hívással átdobja az `src/ui/state/` rétegnek.
- A Flet UI kizárólag ezt az Event réteget figyeli (nem közvetlenül a yt-dlp-t), így az architektúra laza csatolású marad.

## 3. Transzplantációs Források (Amit a RAG-ból átveszünk)

*   **yt-dlp-master (A RAG-ból):** A `PostProcessor` hook-olási struktúrája iránymutató lesz a saját progress callbackünk megírásakor.
*   **ezytdl / GDownloader (A RAG-ból):** A folyamatok szétválasztásának és a "bridge" (vagy websocket/IPC) jellegű UI kommunikációnak a módszertana.
*   **flet-main (A RAG-ból):** A `declarative progress_bar` példa a RAG-ból rávilágított, hogy a Flet state management (`ft.use_state` vagy a klasszikus `update()`) hogyan reagál legjobban a másodpercenkénti frissítésekre aszinkron szálon.

## 4. A Fejlesztés Menetrendje (Action Items)

A RAG adatbázis megismerése után a következő fejlesztési lépéseket fogjuk elvégezni:
1.  Megírjuk a `src/core/downloader.py`-ban az egyéni progress hook metódust, ami tiszta JSON-t/Dict-et generál.
2.  Beállítjuk a `yt_dlp` paramétereit (pl. `{'format': 'bestvideo+bestaudio/best', 'http_headers': ... }`) úgy, hogy felvegye a Sniffer JSON-ját, ha az elérhető.
3.  Implementáljuk az `asyncio` loopot a Queue Managerben a több letöltéses feladatokhoz.
4.  Összekötjük egy minimalista Flet ProgressBarral a folyamatot.