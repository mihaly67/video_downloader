import json
import re
import time
from playwright.sync_api import sync_playwright

def sniffer_poc(url):
    print(f"[*] Indítás: Hálózati megfigyelés ({url})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Külön kontextus indítása, hogy exportálhassuk a Cookie-kat
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        session_data = {
            "media_url": None,
            "headers": {},
            "cookies": [],
            "drm_detected": False
        }

        def handle_response(response):
            nonlocal session_data
            req_url = response.url

            # Logoljuk ki az iframe-eket is, ha a szerver a forrást egy iframe-be tölti.
            # hdmozi gyakran használ beágyazott lejátszókat (pl. vidoza, streamtape, rpmshare, stb.)
            if re.search(r'vidoza|streamtape|voe|mixdrop|uqload|upstream|rpmshare|rpmstream', req_url, re.IGNORECASE):
                print(f"[*] Talált külső szolgáltató iframe URL: {req_url}")
                # Elmentjük iframe URL-nek is, ha netán yt-dlp-nek ez kellene majd.
                if not session_data.get("media_url") and "google" not in req_url and "doubleclick" not in req_url:
                     session_data["media_url"] = req_url
                     session_data["headers"] = response.request.headers

            # 1. Keresés .m3u8 vagy .mpd vagy .mp4 végpontokra
            if re.search(r'\.m3u8|\.mpd|\.mp4', req_url, re.IGNORECASE):
                # Kivétel a hirdetések vagy képek mp4-ei
                if "ad" not in req_url.lower() and "google" not in req_url.lower():
                    print(f"[+] Média Manifeszt/Fájl találat: {req_url}")
                    session_data["media_url"] = req_url
                    session_data["headers"] = response.request.headers

                # Ellenőrizzük a válasz tartalmát (DRM detektálás - MPD)
                try:
                    text_content = response.text()
                    if "ContentProtection" in text_content or "cenc" in text_content or "drm" in text_content.lower():
                        print(f"[WARNING] DRM DETECTED in Manifest - DOWNLOAD MAY FAIL.")
                        session_data["drm_detected"] = True
                    if "EXT-X-KEY" in text_content: # HLS AES encryption (not always DRM, but good to know)
                        print(f"[INFO] HLS Encryption detected (#EXT-X-KEY).")
                except Exception as e:
                    pass

            # 2. Keresés konkrét Widevine licensz kérésekre
            if "widevine" in req_url.lower() or "drm" in req_url.lower():
                print(f"[WARNING] DRM License Request DETECTED: {req_url}")
                session_data["drm_detected"] = True


        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            print("[*] Oldal betöltve. Lejátszás gomb keresése és kattintás...")

            # Megpróbálunk rákattintani a play gombra (Dooplay téma: class="play-pause" vagy hasonló, de a videók iframe mögött is lehetnek)
            try:
                # Often the player requires scrolling into view or evaluating a click via JS
                # Evaluate the click directly on the DOM element to bypass visibility/pointer-events checks
                # hdmozi.hu uses '#clickfakeplayer' and '#player-option-1' elements for the player
                print("[*] JS click kísérlet...")
                page.evaluate("""
                    // Először próbáljuk a szervert választani
                    const serverBtn = document.querySelector('#player-option-1');
                    if (serverBtn) {
                        serverBtn.click();
                    }

                    // Aztán a fake playert
                    setTimeout(() => {
                        const fakePlay = document.querySelector('#clickfakeplayer, .play-pause, .icon-play');
                        if (fakePlay) {
                            fakePlay.click();
                        }
                    }, 1000);
                """)
                print("[+] Play gombra JS kattintás megtörtént (hdmozi/dooplay target).")

            except Exception as e:
                print(f"[!] Hiba a JS kattintás során: {e}")

            # Várakozás a stream elindulására (hálózat figyelése miatt)
            page.wait_for_timeout(10000)

        except Exception as e:
            print(f"[!] Hiba a betöltés során: {e}")

        # Sütik kimentése az aktuális kontextusból
        session_data["cookies"] = context.cookies()

        browser.close()

        # Eredmények mentése fájlba
        with open("session_config.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=4, ensure_ascii=False)

        print("[*] Eredmény elmentve a session_config.json fájlba.")
        return session_data

if __name__ == "__main__":
    # Test URL: A public Dash/HLS stream.
    # We use a public test stream from bitmovin (DRM free for POC, or we can use a DRM one to test the warning)
    # Using a standard HLS test stream first:
    test_url = "https://bitmovin.com/demos/drm" # Ez tartalmaz DRM és nem DRM streamet is a teszt kedvéért.
    sniffer_poc(test_url)
