# Autonomous Subagent Skill: RAG Deep Researcher
# A felhasználó javaslatára: Egy "Kutató Chatbot" az Agent számára.
# Ez a szkript nem egy embert, hanem az LLM-et (Jules-t) szolgálja ki.
# Paraméterként kap egy témát, és autonóm módon (iteratívan) meghívja
# a rag_interrogator.py-t, amíg meg nem találja a legrelevánsabb összefüggő kódokat.
# Majd egy tömörített Markdown/JSON jelentést ad vissza a stdout-on az Agentnek.

import argparse
import subprocess
import os
import json

def autonomous_research(topic: str, max_iterations: int = 3):
    print(f"🤖 [Researcher Subagent] Indítás a '{topic}' témában...")
    script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    interrogator_path = os.path.join(script_dir, "RAG_SYSTEM", "rag_interrogator.py")

    if not os.path.exists(interrogator_path):
        print(f"❌ Hiba: Nem találom a RAG Interrogatort: {interrogator_path}")
        return

    findings = []

    # Iteratív RAG keresés (A "Chatbot" működés szimulációja kódok között)
    for iteration in range(1, max_iterations + 1):
        print(f"🔍 [Researcher Subagent] Iteráció {iteration}/{max_iterations}...")

        # A kutató picit más szavakkal próbálkozik, ha kell (itt most csak limitet növel szimulációként)
        current_limit = iteration * 2
        cmd = [
            "python3", interrogator_path,
            "--query", topic,
            "--limit", str(current_limit)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                # Kinyerjük a fájlneveket a nyers kimenetből, hogy ne bloatoljuk a memóriát
                files_found = [line for line in result.stdout.split('\n') if "📄 FÁJL:" in line]
                for f in files_found:
                    if f not in findings:
                        findings.append(f)
            else:
                 print(f"⚠️ [Researcher Subagent] Hiba az iteráció során: {result.stderr}")
        except subprocess.TimeoutExpired:
             print("⏳ [Researcher Subagent] Időtúllépés a RAG keresésnél!")
             break

    # Visszaadjuk a "Kutató" összefoglalóját az Agentnek
    print("\n📊 --- [KUTATÓ AL-ÜGYNÖK JELENTÉSE] --- 📊")
    if findings:
        print(f"A(z) '{topic}' témában a következő kulcsfájlokat találtam a RAG-ban:")
        for f in findings:
            print(f"  {f.strip()}")
        print("\n💡 Javaslat az Agentnek: Futtasd az interrogator-t a `--filepath` vagy `--expand_file` kapcsolókkal ezeken a fájlokon a teljes kódért!")
    else:
        print(f"Nem találtam egyértelmű kódokat a '{topic}' témában. Próbálj tágabb keresőszót!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Autonomous RAG Researcher Subagent")
    parser.add_argument("--topic", required=True, help="A kutatandó téma (pl. 'yt-dlp hook progress')")
    parser.add_argument("--iterations", type=int, default=2, help="Hány kört fusson a kutató")
    args = parser.parse_args()

    autonomous_research(args.topic, args.iterations)
