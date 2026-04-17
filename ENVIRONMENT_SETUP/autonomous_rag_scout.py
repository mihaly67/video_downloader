import os
import sqlite3
import re
import sys

# Hozzáférés az Agent Memória Menedzserhez (hogy naplózhassuk a találatokat)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ENVIRONMENT_SETUP.agent_memory_manager import write_memory

def run_autonomous_scout():
    """
    Végignyálazza a Video Restauráló RAG adatbázist, és mélyfúrással feltérképezi,
    hogy "mi mire való". Kigyűjti a fájlokat, azok README leírásait,
    vagy az osztályok docstringjeit.
    """
    print("🤖 AUTONÓM FELDERÍTŐ INDÍTÁSA (Deep Drill a Videó Restauráló RAG-on)...")

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "RAG_SYSTEM", "video_downloader_github.db")

    if not os.path.exists(db_path):
        print(f"❌ Adatbázis nem található: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Lekérdezzük az összes fájlt
    try:
        cursor.execute("SELECT source_repo, filepath, file_type, content FROM rag_data ORDER BY source_repo, filepath")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Hiba az SQL lekérdezésben: {e}")
        conn.close()
        return

    print(f"📂 {len(rows)} fájldarab kinyerve az adatbázisból feldolgozásra.")

    repo_insights = {}

    for repo, filepath, file_type, content in rows:
        if not content: continue

        if repo not in repo_insights:
            repo_insights[repo] = {"description": "Nincs elérhető README összegzés.", "files": {}}

        # Fájl szintű feldolgozás
        if filepath not in repo_insights[repo]["files"]:
            repo_insights[repo]["files"][filepath] = ""

        # 1. Repo szintű leírás kinyerése (README.md fájlokból)
        if filepath.endswith("README.md") and file_type.lower() == "documentation":
            # Az első pár mondat a README-ből
            match = re.search(r"#(.*?)(?:\n\n|\Z)", content, re.DOTALL)
            if match:
                desc = match.group(0).strip().replace('\n', ' ')
                # Ha még nagyon rövid, próbálunk kicsit többet
                if len(desc) < 50:
                    lines = content.split('\n')
                    desc = " ".join([l.strip() for l in lines[:10] if l.strip() and not l.startswith('[')])

                # Hozzáadjuk, de csak az első legfontosabb részt (max 500 karakter)
                repo_insights[repo]["description"] = desc[:500] + ("..." if len(desc) > 500 else "")

        # 2. Fájl szintű tudás kinyerése (Python / Kód Docstringek)
        if filepath.endswith(".py"):
            # Keresünk docstringet (tripla idézőjeles kommenteket) ami leírja, mit csinál a fájl/osztály
            doc_match = re.search(r'"""(.*?)"""', content, re.DOTALL)
            if doc_match:
                file_desc = doc_match.group(1).strip().replace('\n', ' ')
                # Csak a lényeget
                repo_insights[repo]["files"][filepath] = file_desc[:200] + ("..." if len(file_desc) > 200 else "")

    conn.close()

    # Jelentés építése
    out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Knowledge_Base", "KNOWLEDGE_MAPS")
    os.makedirs(out_dir, exist_ok=True)
    report_file = os.path.join(out_dir, "video_restoration_deep_drill.md")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 🔬 AUTONÓM MÉLYFÚRÁS (Deep Drill Report)\n")
        f.write("Adatbázis: video_downloader_github.db\n\n")

        for repo in sorted(repo_insights.keys()):
            f.write(f"## 📦 REPO: {repo}\n")
            f.write(f"**Funkció / Leírás:** {repo_insights[repo]['description']}\n\n")
            f.write("**Kritikus Fájlok és Szerepük:**\n")

            # Csak azokat a fájlokat írjuk ki, amiknek sikerült leírást/docstringet kinyerni, vagy nagyon fontos nevük van
            file_count = 0
            for filepath in sorted(repo_insights[repo]["files"].keys()):
                desc = repo_insights[repo]["files"][filepath]
                # Ha van leírása, kiírjuk. Ha nincs, de fontos script (nem __init__.py), akkor is listázzuk.
                if desc:
                    f.write(f"  - 📄 `{filepath}`: *{desc}*\n")
                    file_count += 1
                elif "inference" in filepath or "model" in filepath or "pipeline" in filepath or "train" in filepath:
                     f.write(f"  - 📄 `{filepath}`: (Fő feldolgozó / logikai modul)\n")
                     file_count += 1

            if file_count == 0:
                f.write("  - *(Nincs specifikus dokumentált Python script, valószínűleg csak C/C++ alap vagy nyers modell mappa)*\n")

            f.write("\n" + "-"*40 + "\n\n")

    print(f"\n✅ Autonóm Felderítés befejezve. A teljes térkép a KNOWLEDGE_MAPS mappában: {report_file}")

    # Memória írás (Sűrítve)
    write_memory("Auto_Scout_Report", f"A video restauráló RAG mélyfúrása lefutott. {len(repo_insights)} repository-t elemeztem ki, a teljes jelentés (fájl szintű leírásokkal) a KNOWLEDGE_MAPS/video_restoration_deep_drill.md fájlban van.")

if __name__ == "__main__":
    run_autonomous_scout()
