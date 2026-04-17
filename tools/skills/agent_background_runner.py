# Autonomous Agent Skill: OOM-Safe & Anti-Freeze Background Runner
# (RAG-ból, az 'awesome-llm-apps' scheduler mintájára, Agent specifikus)

import argparse
import subprocess
import time
import os
from concurrent.futures import ThreadPoolExecutor

# Maximum ennyi másodpercig tarthat a script, mielőtt az Executor kilövi (Timeout)
DEFAULT_TASK_TIMEOUT = 3600

def _run_in_thread(task_id: str, command: str, log_dir: str):
    """
    Ez fut a ThreadPoolExecutor egy szálán. Nem blokkolja az Agent fő folyamatát!
    A stdout-ot és stderr-t fájlba írja, ahonnan az Agent UI szaggatás nélkül olvashatja.
    """
    out_file = os.path.join(log_dir, f"{task_id}.out")
    err_file = os.path.join(log_dir, f"{task_id}.err")
    status_file = os.path.join(log_dir, f"{task_id}.status")

    with open(status_file, "w") as f:
        f.write("RUNNING\n")

    print(f"🚀 [Runner] Task {task_id} elindítva a háttérben: '{command}'")

    try:
        with open(out_file, "w") as out_f, open(err_file, "w") as err_f:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=out_f,
                stderr=err_f,
                text=True
            )

            try:
                # Blokkolja EZT A SZÁLAT, amíg le nem fut vagy timeout-ot nem kap
                process.communicate(timeout=DEFAULT_TASK_TIMEOUT)

                if process.returncode == 0:
                    status = "SUCCESS"
                else:
                    status = f"FAILED (Return code: {process.returncode})"

            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate() # Flush remaining IO
                status = f"FAILED (Timeout after {DEFAULT_TASK_TIMEOUT} seconds)"

    except Exception as e:
         status = f"FAILED (Exception: {str(e)})"

    # Frissítjük a státusz fájlt, hogy az Agent UI lássa a végét
    with open(status_file, "w") as f:
        f.write(status + "\n")

    print(f"🏁 [Runner] Task {task_id} befejeződött: {status}")

def submit_task(task_id: str, command: str):
    """
    Beküldi a feladatot a szálkezelőbe. Azonnal visszatér (0.1 mp alatt),
    így a DevBox LLM UI egyetlen másodpercre sem fagy le!
    """
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    os.makedirs(log_dir, exist_ok=True)

    status_file = os.path.join(log_dir, f"{task_id}.status")

    if os.path.exists(status_file):
        with open(status_file, "r") as f:
             current_status = f.read().strip()
             if current_status == "RUNNING":
                 print(f"⚠️ [Runner] A '{task_id}' feladat már fut!")
                 return

    # Létrehozzuk az aszinkron szálat
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_run_in_thread, task_id, command, log_dir)
    # A szálat nem várjuk meg (nem join-oljuk!), hagyjuk a háttérben pörögni
    executor.shutdown(wait=False)

    print(f"✅ [Agent] A '{command}' parancs sikeresen a HÁTTÉRBE küldve!")
    print(f"🧠 [Agent] A folyamat állapotát olvasd a 'cat logs/{task_id}.status' paranccsal!")
    print(f"🧠 [Agent] A kimenetet nézd a 'tail -n 20 logs/{task_id}.out' paranccsal!")

def check_task(task_id: str):
    """Ellenőrzi egy háttérfolyamat állapotát."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
    status_file = os.path.join(log_dir, f"{task_id}.status")

    if not os.path.exists(status_file):
        print(f"❌ Nincs ilyen feladat: {task_id}")
        return

    with open(status_file, "r") as f:
        print(f"📊 Task {task_id} státusz: {f.read().strip()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OOM-Safe Background Task Runner")
    parser.add_argument("--action", choices=["submit", "check"], required=True)
    parser.add_argument("--task_id", required=True, help="Egyedi azonosító a logokhoz (pl. 'video_upscale_1')")
    parser.add_argument("--cmd", type=str, help="A futtatandó shell parancs (csak 'submit' esetén)")
    args = parser.parse_args()

    if args.action == "submit":
        if not args.cmd:
            print("❌ 'submit' esetén a --cmd kötelező!")
        else:
            submit_task(args.task_id, args.cmd)
    elif args.action == "check":
        check_task(args.task_id)
