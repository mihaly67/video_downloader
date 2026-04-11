import faiss
import sqlite3
import numpy as np
import os
import sys
import argparse
from sentence_transformers import SentenceTransformer

def main():
    parser = argparse.ArgumentParser(description="VIDEO DOWNLOADER RAG Query")
    parser.add_argument("--query", type=str, required=True, help="A koncepcionális kérdés (funkció leírása, nem szintaxis)")
    parser.add_argument("--source", type=str, default="", help="SQL Szűrés a 'source' oszlopra (pl. '.py', 'models')")
    parser.add_argument("--limit", type=int, default=5, help="Hány találatot adjon vissza")
    parser.add_argument("--neighborhood", action="store_true", help="Keresse ki a megelőző és következő ROWID-t is a teljes kontextushoz")
    args = parser.parse_args()

    # Mivel minden egy könyvtárban (RAG_SYSTEM) lesz futtatva:
    db_dir = os.path.dirname(os.path.abspath(__file__))

    # A fájlnevek az új struktúra szerint
    index_path = os.path.join(db_dir, "video_downloader_github_compressed.index")
    sqlite_path = os.path.join(db_dir, "video_downloader_github.db")
    model_name = "all-MiniLM-L6-v2"

    # Ha a fájlok nincsenek a helyükön, szólunk a felhasználónak
    if not os.path.exists(index_path):
        print(f"❌ Error: Index file nem található: {index_path}")
        print("💡 Próbáld meg lefuttatni a 'python3 restore_env_vd.py' scriptet!")
        sys.exit(1)
    if not os.path.exists(sqlite_path):
        print(f"❌ Error: SQLite DB nem található: {sqlite_path}")
        print("💡 Próbáld meg lefuttatni a 'python3 restore_env_vd.py' scriptet!")
        sys.exit(1)

    print(f"🧠 Modell betöltése: {model_name}...")
    model = SentenceTransformer(model_name)

    print(f"📂 FAISS Index betöltése: {index_path}...")
    index = faiss.read_index(index_path)

    print(f"🔌 Kapcsolódás SQLite-hoz: {sqlite_path}...")
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    print(f"🎯 Query kódolása: '{args.query}'")
    query_vector = model.encode([args.query]).astype('float32')

    # FAISS Keresés
    k_search = max(500, args.limit * 10)
    print(f"🔍 Vektoros keresés top {k_search} jelöltre...")
    distances, indices = index.search(query_vector, k_search)

    results = []

    for i in range(k_search):
        idx = int(indices[0][i])
        dist = distances[0][i]

        if idx == -1: continue

        # Dinamikus táblanév és oszlop ellenőrzés (támogatja az új 'rag_data/filepath' és a régi 'swat_data/source' sémát is)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]
        table_name = "rag_data" if "rag_data" in tables else ("swat_data" if "swat_data" in tables else (tables[0] if tables else None))

        if not table_name:
            print("❌ Error: Nem található adatokat tartalmazó tábla az SQLite adatbázisban.")
            sys.exit(1)

        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [col[1] for col in cursor.fetchall()]
        source_col = "filepath" if "filepath" in columns else "source"

        if args.source:
            cursor.execute(f"SELECT id, {source_col}, content FROM {table_name} WHERE id=? AND {source_col} LIKE ?", (idx, f"%{args.source}%"))
        else:
            cursor.execute(f"SELECT id, {source_col}, content FROM {table_name} WHERE id=?", (idx,))

        row = cursor.fetchone()
        if row:
            db_id, source_val, content_val = row
            results.append({
                "id": db_id,
                "distance": dist,
                "source": source_val,
                "content": content_val
            })
            if len(results) >= args.limit:
                break


    print("\n" + "="*50)
    print("=== 🎯 RAG INTEL REPORT ===")
    print("="*50 + "\n")

    if not results:
        print("⚠️ Nem találtam egyezést a megadott szűrőkkel.")
    else:
        for i, res in enumerate(results):
            print(f"\n[{i+1}] 📄 SOURCE: {res['source']} | DISTANCE: {res['distance']:.4f} | ROWID: {res['id']}")
            print("-" * 40)

            if args.neighborhood:
                print("--- [ELŐZŐ KONTEXTUS (ROWID-1)] ---")
                try:
                    cursor.execute(f"SELECT content FROM {table_name} WHERE id=?", (res['id'] - 1,))
                    prev_row = cursor.fetchone()
                    if prev_row:
                        print(prev_row[0][:300] + "...\n")
                except Exception as e:
                     print(f"[Hiba az előző kontextus lekérésekor: {e}]")

            print("--- [CÉL KONTEXTUS] ---")
            print(res['content'] + "\n")

            if args.neighborhood:
                print("--- [KÖVETKEZŐ KONTEXTUS (ROWID+1)] ---")
                try:
                    cursor.execute(f"SELECT content FROM {table_name} WHERE id=?", (res['id'] + 1,))
                    next_row = cursor.fetchone()
                    if next_row:
                        print(next_row[0][:300] + "...\n")
                except Exception as e:
                     print(f"[Hiba a következő kontextus lekérésekor: {e}]")

            print("="*50)

    conn.close()

if __name__ == "__main__":
    main()
