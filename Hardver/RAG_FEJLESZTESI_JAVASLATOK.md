# RAG Tudásbázis (Szakkönyvtár) Fejlesztési Javaslatok

Ez a dokumentum a korábbi `repo_list.txt`-ben szereplő repók alapján azonosította azokat a területeket, amelyek hiányoztak a "Video Downloader" alkalmazás RAG tudásbázisából.

A jelenlegi tudásbázis nagyon erős a letöltésben (yt-dlp), a böngésző-automatizációban (Playwright, undetected) és a felületben (Flet), de a kezdeti stádiumban az alábbi területek kiegészítésre szorultak (melyeket az **új repo lista** már javarészt tartalmaz is):

## 1. DRM és Decryption (Titkosítás feloldás / PSSH elemzés)
*   **Hiányzó tudás:** Widevine L3 CDM kezelés, PSSH (Protection System Specific Header) boxok bináris kinyerése a Manifestből, kulcsok származtatása.
*   **Javasolt Repók betáplálásra:**
    *   `pywidevine` vagy WVD extractorok.
    *   `shaka-packager` (A Google eszköze az MPD-k elemzésére).
    *   `Bento4` (`mp4decrypt` integrálása a Python workflow-ba).

## 2. Network Intercept & Proxying (Mély hálózati lehallgatás)
*   **Hiányzó tudás:** Programozható HTTPS proxy réteg beiktatása TLS/SSL pinning vagy WebSockets esetén.
*   **Javasolt Repók betáplálásra:**
    *   `mitmproxy` (Python alapú profi proxy, ami on-the-fly dekódol).
    *   `selenium-wire`.

## 3. M3U8 / DASH Manifest Python Parser
*   **Hiányzó tudás:** Manifeszt fájlok strukturált, objektum-orientált szétszedése memóriában történő manipuláláshoz.
*   **Javasolt Repók betáplálásra:**
    *   `m3u8` (globez/m3u8 - a de facto standard Python parser).
    *   `dash-parser` vagy specifikus MPD parserek.

## 4. JavaScript Reverse Engineering Tools (AST/WebAssembly)
*   **Hiányzó tudás:** JS AST módosítás Pythonból, memóriaszivárgások és rejtett kulcsok kinyerése (pl. JScrambler ellen).
*   **Javasolt Repók betáplálásra:**
    *   `slimit` vagy bármilyen más Python JS AST analizátor.
    *   WebAssembly reverse engineering repók (mivel egyre több lejátszó WASM modulokba rejti a kriptográfiai kulcsokat).

---
**Összegzés (Update):**
Az új repólista (`repo_list.txt`) vizsgálata alapján kijelenthető, hogy a RAG adatbázis forrásai közé sikeresen bekerültek a fent javasolt kulcsfontosságú elemek (pl. `Bento4`, `shaka-packager`, `mitmproxy`, `m3u8-master`, `playwright_stealth-main`). Ezen technológiák integrálása lehetővé teszi az Agent (Jules) számára a fejlett videóletöltő motor felépítését.