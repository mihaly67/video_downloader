import os
import sys
import subprocess

# --- 1. FÜGGŐSÉGEK TELEPÍTÉSE (AUTO-INSTALL) ---
def install_dependencies():
    print("🔧 Függőségek ellenőrzése és telepítése...")
    required = [
        "colorama"
    ]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            print(f"   ⚠️ '{pkg}' hiányzik. Telepítés...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg], stdout=subprocess.DEVNULL)
                print(f"   ✅ '{pkg}' telepítve.")
            except Exception as e:
                print(f"   ❌ Hiba a(z) '{pkg}' telepítésekor: {e}")

install_dependencies()

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore: GREEN=""; RED=""; YELLOW=""; CYAN=""; RESET=""
    class Style: BRIGHT=""

# --- KONFIGURÁCIÓ ---
ENVIRONMENT_RESOURCES = {
    "VIDEO_DOWNLOADER_RAG": {
        "drive_link": "https://drive.google.com/file/d/14axP0bV62AehyynYSswpN9apfAcwly4M/view?usp=sharing",
        "vps_path": "/home/misi/video_downloader_RAG",
        "description": "A RAG rendszer a VPS-en (5.189.163.88) él. Helyi letöltés letiltva az erőforrások kímélése végett."
    },
    "RAG_buider_agents_skill_dev_RAG": {
        "drive_link": "https://drive.google.com/file/d/1hNl4JYrms427u94H48kpkb39OJ5C5AhN/view?usp=sharing",
        "vps_path": "/home/misi/Rag_epites, chatbot_csv_data_llm_RAG",
        "description": "A RAG rendszer a VPS-en (5.189.163.88) él. Helyi letöltés letiltva az erőforrások kímélése végett."
    }
}

def log(msg, color=Fore.GREEN):
    print(f"{color}{msg}{Style.RESET_ALL}")

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
    print(f"{Fore.CYAN}=== 🚀 VIDEO DOWNLOADER KÖRNYEZET DEPLOYMENT ==={Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}ℹ️ RAG INFO: A RAG adatbázisok lokális letöltése deaktiválva. Hozzáférés kizárólag a VPS-en keresztül (vps_bridge.py).{Style.RESET_ALL}")
    for key, config in ENVIRONMENT_RESOURCES.items():
        print(f"   - {key}: {config['vps_path']}")

    update_gitignore()
    print(f"\n{Fore.GREEN}✅ KÖRNYEZET KÉSZ.{Style.RESET_ALL}")


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


    # Heartbeat indítása háttérben
    print(f"\n{Fore.YELLOW}💓 Agent Heartbeat (Keep-Alive Daemon) indítása...{Style.RESET_ALL}")
    heartbeat_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ENVIRONMENT_SETUP", "heartbeat.py")
    if os.path.exists(heartbeat_script):
        try:
            subprocess.Popen([sys.executable, "-u", heartbeat_script])
        except Exception as e:
            print(f"{Fore.RED}❌ Hiba a Heartbeat indításakor: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ A Heartbeat script nem található a várt helyen: {heartbeat_script}{Style.RESET_ALL}")

    # Health Check futtatása
    print(f"\n{Fore.YELLOW}🩺 Agent System Health Check ellenőrzése...{Style.RESET_ALL}")
    checker_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ENVIRONMENT_SETUP", "agent_health_checker.py")
    if os.path.exists(checker_script):
        try:
            subprocess.run([sys.executable, checker_script])
        except Exception as e:
            print(f"{Fore.RED}❌ Hiba a Health Check futtatásakor: {e}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ A Health Check script nem található a várt helyen: {checker_script}{Style.RESET_ALL}")



if __name__ == "__main__":
    main()
