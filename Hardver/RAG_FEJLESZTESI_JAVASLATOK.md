# RAG Tudásbázis (Szakkönyvtár) Fejlesztési Javaslatok

Ez a dokumentum a `repo_list.txt`-ben szereplő repók alapján azonosítja azokat a területeket, amelyek jelenleg hiányoznak a "Video Downloader" alkalmazás RAG (Retrieval-Augmented Generation) tudásbázisából. Ezen repók jövőbeli betáplálása a rendszerbe elengedhetetlen a professzionális, minden streaming oldalra kiterjedő letöltőmotor megalkotásához.

A jelenlegi tudásbázis nagyon erős a letöltésben (yt-dlp), a böngésző-automatizációban (Playwright, undetected) és a felületben (Flet), de az alábbi területek kiegészítésre szorulnak:

## 1. DRM és Decryption (Titkosítás feloldás / PSSH elemzés)
Jelenleg a rendszer tudja letölteni a kódolatlan fájlokat (vagy a `N_m3u8DL-RE` segít), de a specifikus DRM technológiákhoz hiányzik a kód-szintű Python tudás.
*   **Hiányzó tudás:** Widevine L3 CDM kezelés, PSSH (Protection System Specific Header) boxok bináris kinyerése a Manifestből, kulcsok származtatása.
*   **Javasolt Repók betáplálásra:**
    *   `pywidevine` vagy WVD (Widevine Device) extractorok.
    *   `shaka-packager` (A Google eszköze az MPD-k elemzésére).
    *   `Bento4` (`mp4decrypt` integrálása a Python workflow-ba).

## 2. Network Intercept & Proxying (Mély hálózati lehallgatás)
A Playwright `page.on('request')` funkciója jó, de előfordulhat, hogy TLS/SSL pinning van egy iframe-ben, vagy a JS kód WebSocket-eket használ a kulcscseréhez, amit a Playwright nem mindig lát transzparensen.
*   **Hiányzó tudás:** Programozható HTTPS proxy réteg beiktatása.
*   **Javasolt Repók betáplálásra:**
    *   `mitmproxy` (Python alapú profi proxy, ami on-the-fly dekódol).
    *   `selenium-wire` (olyan automatizáció, amely kiterjeszti a hálózati rétegek láthatóságát).

## 3. M3U8 / DASH Manifest Python Parser
Ha a `yt-dlp` valamiért nem birkózik meg egy egyedi manifeszttel (pl. beágyazott, hamis megszakításos hirdetések, trükkös redirectek), akkor szükség lehet a `.m3u8` vagy `.mpd` fájl Python-on belüli, memóriában történő manipulálására letöltés előtt.
*   **Hiányzó tudás:** Manifeszt fájlok strukturált, objektum-orientált szétszedése.
*   **Javasolt Repók betáplálásra:**
    *   `m3u8` (globez/m3u8 - a de facto standard Python parser).
    *   `dash-parser` vagy specifikus MPD parserek.

## 4. JavaScript Reverse Engineering Tools (AST/WebAssembly)
A listában szereplő `js-beautify` hasznos formázásra, de a modern obfuszkátorok (pl. Eval unpacking, string-szótáras rejtés, JScrambler) ellen programozott AST (Abstract Syntax Tree) elemzésre lenne szükség a tokenek kiszedéséhez.
*   **Hiányzó tudás:** JS AST módosítás Pythonból, memóriaszivárgások és rejtett kulcsok kinyerése.
*   **Javasolt Repók betáplálásra:**
    *   `slimit` vagy bármilyen más Python JS AST analizátor.
    *   WebAssembly reverse engineering repók (mivel egyre több lejátszó WASM modulokba rejti a kriptográfiai kulcsokat).

---
**Összegzés:**
A fent említett technológiák integrálása a RAG-ba lehetővé tenné az Agent (Jules) számára, hogy önállóan képes legyen feltörni és visszafejteni a "kölcsönvehetetlen" stream architektúrákat is.
