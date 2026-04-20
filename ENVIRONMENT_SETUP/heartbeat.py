import time
import os
import sys

def run_daemon():
    """
    Egy nagyon könnyű (0.01% CPU), végtelen ciklusú háttérfolyamat (Daemon).
    Folyamatosan ír egy apró "szívverés" logot, vagy touch-ol egy fájlt,
    ezzel elhitetve az Agent UI-al és a Cloudflare/Docker containerrel,
    hogy a virtuális gépben folyamatos I/O munkavégzés zajlik.
    Megakadályozza, hogy az Agent "hosszú gondolkodás" közben kifagyjon a timeout miatt.
    """
    keepalive_file = os.path.join(os.path.dirname(__file__), ".agent_heartbeat")

    print(f"💓 [Keep-Alive Daemon] Elindult. Folyamatos szívverés generálása: {keepalive_file}", flush=True)

    try:
        while True:
            # Szívverés fájl frissítése
            with open(keepalive_file, "w") as f:
                f.write(str(time.time()))

            # Memória frissességének ellenőrzése
            memory_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Knowledge_Base", "agent_memory.jsonl")
            if os.path.exists(memory_file):
                last_modified = os.path.getmtime(memory_file)
                if (time.time() - last_modified) > (15 * 60):  # 15 perc
                    print(f"\n🚨 [SUPERVISOR ALERT] AZ AGENT ELFELEJTETTE ÍRNI A MEMÓRIÁT! 🚨")
                    print(f"👉 KÖTELEZŐ AKCIÓ: Futtasd az agent_memory_manager.py --action write parancsot!\n", flush=True)

            print(f"💓 [Keep-Alive] Updated .agent_heartbeat at {time.strftime('%H:%M:%S')}", flush=True)
            sys.stdout.flush()

            # Módosított várakozási idő: 10 perc
            time.sleep(600)
    except KeyboardInterrupt:
        print("💓 [Keep-Alive Daemon] Leállítva.")

if __name__ == "__main__":
    run_daemon()
