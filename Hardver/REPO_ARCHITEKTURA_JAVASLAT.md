# Video Downloader Projekt: Bővített Repository Lista és Architektúra Javaslat

Ez a dokumentum a jelenlegi tudásbázis (RAG) felépítéséhez szánt GitHub repository-k listáját és az "Ördög Ügyvédje" (Jules) által javasolt jövőálló kiegészítéseket tartalmazza.

## 1. Az eredeti lista elemzése
A kapott `repo_list.txt` alaposan felkészült a "nyers letöltésre", dekonstrukcióra és a bot-védelem kijátszására:
*   **Letöltés & Stream:** `yt-dlp-master`, `youtube-dl-master`, `N_m3u8DL-RE-main`, `metube-master`
*   **Bot-védelem kicselezése (Anti-Fingerprint):** `playwright-python-main`, `undetected-chromedriver-master`, `undetected-playwright-python-main`, `puppeteer-extra-master`, `fingerprintjs-master`, `fingerprint-suite-master`
*   **Dekódolás & Konvertálás:** `FFmpeg-master`, `FFmpeg-Builds-master`
*   **Visszafejtés (Obfuszkáció):** `jadx-master` (Android APK elemzés API végpontokért), `js-beautify-main` (Tömörített JS logika olvashatóvá tétele)
*   **GUI:** `flet-main`
*   **AI (Korlátozott):** `bloom-master` (A Bloom AI nyelvmodellje, valószínűleg szöveges értelmezésre)

## 2. Javasolt kiegészítések (Az "Ördög Ügyvédjétől" és Gemini számára)

Tekintettel az extrém bonyolult (szétválasztott, DRM-es, dinamikusan változó DOM-ú) streamekre, valamint az AI integrációra (különösen a korlátozott CPU-s VPS környezetben), az alábbi repókat/könyvtárakat JAVASLOM a RAG tudásbázisba beemelni a generálás előtt:

### A. Szegmentált és Nehéz Streamek (HLS/DASH/DRM) mélyebb analízise
1.  **`globocom/m3u8`** (Python): A végtelenségig darabolt, eltérített `.m3u8` lejátszási listák professzionális, objektum-orientált feldolgozásához (pl. kulcsok, reklám-chunkok szűrése).
2.  **`shaka-project/shaka-packager`**: Szükséges megérteni, hogyan építik fel a CENC (Widevine/PlayReady) titkosított `.mpd` (DASH) fájlokat. Ez segít felismerni azokat a streameket, amiket *nem* tudunk letölteni, így kíméljük az erőforrásokat.
3.  **`Bento4/Bento4`**: A legfejlettebb MP4 és MPEG-DASH parancssori eszközkészlet. Elengedhetetlen, ha az ffmpeg elakad egy furcsán csomagolt fragmented mp4 (`.m4s`) fájllal.

### B. AI és Kép/Hang felismerés (A Captcha és OCR problémákra)
A VPS CPU-ja gyenge (3 mag). Ezért olyan optimalizált AI repók kellenek, amik C++ alapúak és CPU-n is jól futnak:
1.  **`ggerganov/whisper.cpp`**: Az OpenAI Whisper C++ portja. Extrém memóriatakarékos, CPU-n is futtatható. Ha a videó letöltő egy audio captchába (pl. reCaptcha hangos verzió) fut, ezzel át tudja billenteni az automatizációt.
2.  **`JaidedAI/EasyOCR`**: Könnyűsúlyú, Python alapú optikai karakterfelismerő (OCR). Hasznos lehet, ha a lejátszó "Play" gombja vagy egy hivatkozás egy képen van elrejtve, és JavaScriptből nem olvasható ki.

### C. Fejlett Proxy és Hálózat
1.  **`mitmproxy/mitmproxy`**: A böngészőből történő letöltés (Playwright) sokszor nem elég, ha a stream Websocketeken vagy nagyon bonyolult protokollokon jön. A mitmproxy Python API-jával a háttérben elemezhető és manipulálható a teljes TLS titkosított forgalom.

## 3. RAG Generálási Javaslat a VPS-en
Mivel a felhasználó jelezte, hogy a RAG adatbázist a VPS-en fogja elkészíteni (hogy kímélje a jelenlegi környezetet), az alábbi paramétereket javaslom a `rag_builder.py`-ben beállítani a gyenge CPU (3 mag, 8GB RAM) miatt:
*   `BATCH_SIZE` csökkentése (pl. `50`-re a jelenlegi 100-ról).
*   Az indexelés lassú lesz az `all-MiniLM-L6-v2` modellel CPU-n. Érdemes a futtatást "screen" vagy "tmux" alól indítani az Ubuntu szerveren, hogy SSH szakadás esetén is folytatódjon.
*   Figyelni kell a RAM használatot, a Faiss index memóriaigényes tud lenni.

---
*Készítette: Jules (Agent)*