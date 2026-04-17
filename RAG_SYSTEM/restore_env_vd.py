import os
import sys
import shutil
import zipfile
import subprocess
import json
import sqlite3
import glob

# --- 1. FÜGGŐSÉGEK TELEPÍTÉSE (AUTO-INSTALL) ---
def install_dependencies():
    print("🔧 Függőségek ellenőrzése és telepítése...")
    required = [
        "gdown",
        "faiss-cpu",
        "sentence-transformers",
        "numpy",
        "pandas",
        "colorama"
    ]
    for pkg in required:
        try:
            module_name = pkg
            if pkg == "sentence-transformers":
                module_name = "sentence_transformers"
            elif pkg == "faiss-cpu":
                module_name = "faiss"

            __import__(module_name.replace("-", "_"))
        except ImportError:
            print(f"   ⚠️ '{pkg}' hiányzik. Telepítés...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
                print(f"   ✅ '{pkg}' telepítve.")
                if pkg == "playwright":
                    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium", "--quiet"])
            except Exception as e:
                print(f"   ❌ Hiba a(z) '{pkg}' telepítésekor: {e}")

install_dependencies()

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore: GREEN=""; RED=""; YELLOW=""; CYAN=""; RESET=""
    class Style: BRIGHT=""

try:
    import gdown
    import asyncio
    from playwright.async_api import async_playwright
except ImportError:
    pass

# --- KONFIGURÁCIÓ ---
# Mivel a RAG fájlok a script mellett, a RAG_SYSTEM mappában kell landoljanak:
ENVIRONMENT_RESOURCES = {
    "VIDEO_DOWNLOADER_RAG": {
        "id": "14axP0bV62AehyynYSswpN9apfAcwly4M", # A legújabb kibővített RAG adatbázis (136 MB)
        "file": "video_downloader_knowledge.zip",
        "extract_to": os.path.dirname(os.path.abspath(__file__)),
        "check_file": "video_downloader_github.db",
        "type": "zip",
        "preserve_dir": False
    },
    "RAG_buider_agents_skill_dev_RAG": {
        "id": "1hNl4JYrms427u94H48kpkb39OJ5C5AhN",
        "file": "rag_builder_agents_skill_dev_rag.zip",
        "extract_to": os.path.dirname(os.path.abspath(__file__)),
        "check_file": "RAG_CHATBOT_CSV_DATA_LLM_github.db",
        "type": "zip",
        "preserve_dir": False
    }

}

# Dinamikusan felülírjuk az ID-t a környezeti változó alapján
env_rag_id = os.environ.get("video_downloader_RAG")
if env_rag_id:
    # Ha teljes URL-t kaptunk, kiszedjük az ID-t
    if "id=" in env_rag_id:
        ENVIRONMENT_RESOURCES["VIDEO_DOWNLOADER_RAG"]["id"] = env_rag_id.split("id=")[1].split("&")[0]
    elif "/d/" in env_rag_id:
        ENVIRONMENT_RESOURCES["VIDEO_DOWNLOADER_RAG"]["id"] = env_rag_id.split("/d/")[1].split("/")[0]
    else:
        ENVIRONMENT_RESOURCES["VIDEO_DOWNLOADER_RAG"]["id"] = env_rag_id

env_builder_id = os.environ.get("RAG_buider_agents_skill_dev_RAG")
if env_builder_id:
    if "id=" in env_builder_id:
        ENVIRONMENT_RESOURCES["RAG_buider_agents_skill_dev_RAG"]["id"] = env_builder_id.split("id=")[1].split("&")[0]
    elif "/d/" in env_builder_id:
        ENVIRONMENT_RESOURCES["RAG_buider_agents_skill_dev_RAG"]["id"] = env_builder_id.split("/d/")[1].split("/")[0]
    else:
        ENVIRONMENT_RESOURCES["RAG_buider_agents_skill_dev_RAG"]["id"] = env_builder_id

def log(msg, color=Fore.GREEN):
    print(f"{color}{msg}{Style.RESET_ALL}")

def hoist_files(target_dir, check_file):
    if not check_file: return False

    found_path = None
    for root, dirs, files in os.walk(target_dir):
        if check_file in files:
            found_path = os.path.join(root, check_file)
            break
    if not found_path: return False

    source_dir = os.path.dirname(found_path)
    if os.path.abspath(source_dir) == os.path.abspath(target_dir): return True

    log(f"   ⬆️ Fájlok felmozgatása innen: {source_dir}", Fore.CYAN)
    for item in os.listdir(source_dir):
        try:
            shutil.move(os.path.join(source_dir, item), os.path.join(target_dir, item))
        except: pass

    try:
        if not os.listdir(source_dir):
            os.rmdir(source_dir)
    except: pass

    return True

def check_sqlite_integrity(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return bool(tables)
    except sqlite3.Error:
        return False

async def playwright_download_fallback(drive_id, output_path):
    """Playwright alapú letöltés (a Google Drive 'Virus scan warning' oldalának megkerüléséhez)."""
    url = f"https://drive.google.com/uc?export=download&id={drive_id}"
    dest_path = os.path.abspath(output_path)

    log(f"   🤖 Playwright böngésző indítása a Google Drive limitációinak megkerülésére...", Fore.YELLOW)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            async with page.expect_download(timeout=120000) as download_info:
                await page.goto(url)

                try:
                    await page.click("input[type='submit']", timeout=5000)
                    log("   🖱️ 'Download anyway' gomb lekattintva.", Fore.CYAN)
                except Exception:
                    pass # Nincs gomb, a letöltés automatikusan indult

            download = await download_info.value
            await download.save_as(dest_path)
            await browser.close()

            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1024:
                return True
            return False
    except Exception as e:
        log(f"   ❌ Playwright hiba: {e}", Fore.RED)
        return False

def process_resource(key, config):
    print(f"\n🔧 Feldolgozás: {key}...")

    target_dir = config.get("extract_to")
    check_file = config.get("check_file")
    zip_name = config["file"]
    drive_id = config["id"]
    preserve_dir = config.get("preserve_dir", False)

    check_path = os.path.join(target_dir, check_file) if check_file and target_dir else None

    # 1. Ellenőrzés: Létezik és ép?
    is_valid = False
    if check_path and os.path.exists(check_path):
        if check_path.endswith(".db") or check_path.endswith(".sqlite"):
            is_valid = check_sqlite_integrity(check_path)
        else:
            is_valid = os.path.getsize(check_path) > 1024

    if is_valid:
        log(f"   ✅ {key} rendben (Ellenőrizve).")
        return

    # Törlés és újraletöltés
    if check_path and os.path.exists(check_path) and not preserve_dir:
        log(f"   ⚠️ {key} sérült vagy érvénytelen. Törlés és újraletöltés...", Fore.YELLOW)
        try:
            if os.path.isdir(target_dir): shutil.rmtree(target_dir)
        except: pass
    elif not os.path.exists(target_dir):
        log(f"   ⚠️ {key} célkönyvtára ({target_dir}) nem létezik. Létrehozás...", Fore.YELLOW)

    # 2. Letöltés
    if not os.path.exists(zip_name):
        log(f"   📥 Letöltés: {zip_name} (ID: {drive_id})...", Fore.CYAN)
        try:
            # First try with gdown
            res = gdown.download(id=drive_id, output=zip_name, quiet=False)
            if res is None:
                raise Exception("A gdown nem kapott érvényes fájlt (valószínűleg Virus scan warning).")
        except Exception as e:
            log(f"   ⚠️ Hagyományos letöltés sikertelen ({e}).", Fore.YELLOW)
            try:
                success = asyncio.run(playwright_download_fallback(drive_id, zip_name))
                if not success:
                    log(f"   ❌ Végleges letöltési hiba.", Fore.RED)
                    return
            except NameError:
                log(f"   ❌ Playwright nincs telepítve, letöltés megszakítva.", Fore.RED)
                return

    # 3. Kicsomagolás
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
        log(f"   📦 Kicsomagolás ide: {target_dir}...", Fore.CYAN)
        try:
            with zipfile.ZipFile(zip_name, 'r') as z:
                z.extractall(target_dir)

            if check_file:
                hoist_files(target_dir, check_file)
                final_check_path = os.path.join(target_dir, check_file)
                if not os.path.exists(final_check_path):
                     log(f"   ❌ Hiba: {check_file} nem található kicsomagolás után sem!", Fore.RED)
                else:
                     log(f"   ✨ {key} Sikeresen telepítve.", Fore.GREEN)

        except zipfile.BadZipFile:
            log("   ❌ Sérült Zip Fájl! Törlés...", Fore.RED)
            os.remove(zip_name)
        except Exception as e:
            log(f"   ❌ Kicsomagolási hiba: {e}", Fore.RED)
        finally:
            if os.path.exists(zip_name):
                os.remove(zip_name)

def update_gitignore():
    print("\n📝 .gitignore frissítése...")
    ignore_entry = "Knowledge_Base/"

    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            content = f.read()

        if ignore_entry not in content:
            with open(".gitignore", "a") as f:
                f.write(f"\n# RAG Database (FAISS)\n{ignore_entry}\n")
            log(f"   ✅ Hozzáadva: {ignore_entry}", Fore.GREEN)
        else:
            log(f"   ℹ️ Már tartalmazza: {ignore_entry}", Fore.CYAN)
    else:
        with open(".gitignore", "w") as f:
            f.write(f"# RAG Database (FAISS)\n{ignore_entry}\n")
        log(f"   ✅ Létrehozva és hozzáadva: {ignore_entry}", Fore.GREEN)

def main():
    print(f"{Fore.CYAN}=== 🚀 VIDEO DOWNLOADER RAG (FAISS + SQLITE) DEPLOYMENT ==={Style.RESET_ALL}")

    for key, config in ENVIRONMENT_RESOURCES.items():
        process_resource(key, config)

    update_gitignore()
    print(f"\n{Fore.GREEN}✅ KÖRNYEZET KÉSZ. RAG RENDSZER AKTÍV.{Style.RESET_ALL}")

    # Automatikus memória indítás
    print(f"\n{Fore.YELLOW}🧠 Agent Memory Manager inicializálása...{Style.RESET_ALL}")
    memory_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ENVIRONMENT_SETUP", "agent_memory_manager.py")
    if os.path.exists(memory_script):
        try:
            subprocess.run([sys.executable, memory_script, "--action", "start_session"])
        except Exception as e:
            print(f"{Fore.RED}❌ Hiba az Agent Memory indításakor: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ Az Agent Memory Manager nem található a várt helyen: {memory_script}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
