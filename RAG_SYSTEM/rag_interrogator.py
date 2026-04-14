import faiss
import sqlite3
import numpy as np
import os
import sys
import argparse
from sentence_transformers import SentenceTransformer

def main():
    parser = argparse.ArgumentParser(description="SWAT RAG Interrogator - Deep Drill Edition")
    parser.add_argument("--query", type=str, required=True, help="A koncepcionális kérdés (funkció leírása, ne kód)")
    parser.add_argument("--category", type=str, default="", help="Szűrés kategóriára (pl. 'ML_Ops', 'Black_Ops')")
    parser.add_argument("--repo", type=str, default="", help="Szűrés repóra (pl. 'HellsGate')")
    parser.add_argument("--filepath", type=str, default="", help="Szűrés adott fájlnévre vagy útvonalra")
    parser.add_argument("--limit", type=int, default=3, help="Hány találatot adjon vissza (alap: 3)")
    parser.add_argument("--neighborhood", type=int, default=0, help="Hány előző és következő blokkot fűzzön hozzá a találathoz (pl. 2)")
    parser.add_argument("--expand_file", action="store_true", help="KASZKÁD FÚRÁS: Újraépíti az egész fájlt, amelyben a találat szerepel")
    args = parser.parse_args()

    # Próbáljuk megtalálni az aktuális adatbázist
    db_dir = os.path.dirname(os.path.abspath(__file__))
    index_path = os.path.join(db_dir, "video_downloader_github_compressed.index")
    sqlite_path = os.path.join(db_dir, "video_downloader_github.db")

    if not os.path.exists(index_path) or not os.path.exists(sqlite_path):
        print(f"❌ Error: Nem találtam érvényes RAG adatbázist a {db_dir} mappában.")
        print("💡 Próbáld meg lefuttatni a 'python3 RAG_SYSTEM/restore_env_vd.py' scriptet!")
        sys.exit(1)

    print(f"🧠 Modell betöltése (all-MiniLM-L6-v2)...")
    # Csendesebb modell betöltés
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"📂 FAISS Index: {index_path}")
    index = faiss.read_index(index_path)

    print(f"🔌 SQLite DB: {sqlite_path}")
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Ellenőrizzük a tábla sémáját, hogy a régi vagy az új van-e (visszafelé kompatibilitás)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rag_data'")
    is_new_schema = cursor.fetchone() is not None

    print(f"🎯 Query kódolása: '{args.query}'")
    query_vector = model.encode([args.query]).astype('float32')

    k_search = max(1000, args.limit * 50)
    print(f"🔍 Vektoros keresés top {k_search} jelöltre...")
    distances, indices = index.search(query_vector, k_search)

    results = []

    # Dinamikus table name lekérés függetlenül az is_new_schema checktől (hogy a table_name globálisan elérhető legyen)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]
    table_name = "rag_data" if "rag_data" in tables else ("swat_data" if "swat_data" in tables else (tables[0] if tables else None))

    if not table_name:
        print("❌ Error: Nem található adatokat tartalmazó tábla az SQLite adatbázisban.")
        sys.exit(1)

    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = [col[1] for col in cursor.fetchall()]
    source_col = "filepath" if "filepath" in columns else "source"

    # SQL alapok a séma függvényében
    if is_new_schema:
        sql_base = "SELECT id, 'Unknown', 'Unknown', filepath, content FROM rag_data WHERE id=?"
    else:
        sql_base = f"SELECT id, 'Unknown', 'Unknown', {source_col}, content FROM {table_name} WHERE id=?"

    sql_params = []

    if True: # apply filter regardless of schema if possible
        if args.filepath:
            sql_base += f" AND {source_col if not is_new_schema else 'filepath'} LIKE ?"
            sql_params.append(f"%{args.filepath}%")

    for i in range(k_search):
        idx = int(indices[0][i])
        dist = distances[0][i]

        if idx == -1: continue

        cursor.execute(sql_base, [idx] + sql_params)
        row = cursor.fetchone()

        if row:
            db_id, category, source_repo, filepath, content = row

            # Ne adjunk vissza olyan fájlokat amiket már megtaláltunk ha expand_file aktív (deduplikáció)
            if args.expand_file and any(r['filepath'] == filepath for r in results):
                continue

            results.append({
                "id": db_id,
                "distance": dist,
                "category": category,
                "repo": source_repo,
                "filepath": filepath,
                "content": content
            })
            if len(results) >= args.limit:
                break

    print("\n" + "═"*80)
    print("🎯 RAG INTEL REPORT - DEEP DRILL EDITION 🎯")
    print("═"*80 + "\n")

    if not results:
        print("⚠️ Nem találtam egyezést a megadott vektoros és metaadat szűrőkkel.")
    else:
        for i, res in enumerate(results):
            print(f"[{i+1}] 📄 FÁJL: {res['filepath']}")
            print(f"    🏷️ KATEGÓRIA: {res['category']} | 📦 REPO: {res['repo']} | 📏 TÁVOLSÁG: {res['distance']:.4f} | 🔑 CÉL-ROWID: {res['id']}")
            print("-" * 80)

            # a `table_name` már fent be lett állítva a `is_new_schema` vagy a fallback alapján

            # ---------------------------------------------------------
            # 1. KASZKÁD / EXPAND_FILE MÓD (A teljes fájl visszaállítása)
            # ---------------------------------------------------------
            if args.expand_file and res['filepath'] != 'Unknown':
                print(f"🔄 KASZKÁD FÚRÁS AKTÍV: A teljes '{res['filepath']}' fájl rekonstruálása...")
                # Kiszedjük az adott fájlhoz tartozó összes rekordot ROWID szerint sorbarendezve
                if is_new_schema:
                    cursor.execute(f"SELECT content FROM {table_name} WHERE filepath = ? ORDER BY id ASC",
                                   (res['filepath'],))
                else:
                    cursor.execute(f"SELECT content FROM {table_name} WHERE {source_col} = ? ORDER BY id ASC",
                                   (res['filepath'],))

                all_chunks = cursor.fetchall()

                if all_chunks:
                    print(f"   ✓ {len(all_chunks)} adatbázis blokk összefűzve.\n")
                    print("⬇️ --- [REKONSTRUÁLT FÁJL KEZDETE] --- ⬇️\n")

                    full_text = ""
                    for chunk in all_chunks:
                        # Ha van overlap (átfedés), egy okosabb összefűzés is lehetséges lenne, de
                        # az egyszerűség kedvéért egyelőre csak kiírjuk őket egymás után egy vizuális elválasztóval.
                        full_text += chunk[0] + "\n...[CHUNK_BOUNDARY]...\n"

                    print(full_text)
                    print("⬆️ --- [REKONSTRUÁLT FÁJL VÉGE] --- ⬆️\n")
                else:
                    print("⚠️ Hiba a fájl rekonstruálása közben.")

            # ---------------------------------------------------------
            # 2. SZOMSZÉDSÁG / NEIGHBORHOOD MÓD (Kibővített kontextus)
            # ---------------------------------------------------------
            elif args.neighborhood > 0:
                print(f"🔍 SZOMSZÉDSÁG AKTÍV (±{args.neighborhood} blokk)")

                # Előző blokkok lekérdezése
                cursor.execute(f"SELECT id, content FROM {table_name} WHERE id >= ? AND id < ? ORDER BY id ASC",
                               (res['id'] - args.neighborhood, res['id']))
                prev_rows = cursor.fetchall()

                for pr_id, pr_content in prev_rows:
                    print(f"--- [ELŐZŐ KONTEXTUS (ROWID: {pr_id})] ---")
                    print(pr_content + "\n")

                print(f"--- [🎯 CÉL KONTEXTUS (ROWID: {res['id']})] ---")
                print(res['content'] + "\n")

                # Következő blokkok lekérdezése
                cursor.execute(f"SELECT id, content FROM {table_name} WHERE id > ? AND id <= ? ORDER BY id ASC",
                               (res['id'], res['id'] + args.neighborhood))
                next_rows = cursor.fetchall()

                for nx_id, nx_content in next_rows:
                    print(f"--- [KÖVETKEZŐ KONTEXTUS (ROWID: {nx_id})] ---")
                    print(nx_content + "\n")

            # ---------------------------------------------------------
            # 3. NORMÁL MÓD (Csak a cél chunk)
            # ---------------------------------------------------------
            else:
                print("--- [CÉL KONTEXTUS] ---")
                print(res['content'] + "\n")
                print("💡 Tipp: Használd a '--neighborhood 2' vagy '--expand_file' kapcsolókat a teljesebb képért!")

            print("═"*80 + "\n")

    conn.close()

if __name__ == "__main__":
    main()
