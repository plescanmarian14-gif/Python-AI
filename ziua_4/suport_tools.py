import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# 1. Încărcăm .env din același folder
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


# 2. Funcția Tool
def cauta_status_comanda(id_comanda: str) -> str:
    """Caută statusul unei comenzi în baza de date după ID-ul ei.

    Args:
        id_comanda: ID-ul unic al comenzii (ex: #1042 sau 1042).
    """
    baza_date = {
        "1042": "Expediată (Aflată în tranzit cu Fan Courier, AWB: 994821)",
        "1043": "În procesare la depozit",
        "1044": "Anulată (Plată eșuată)",
    }
    curatat = id_comanda.replace("#", "").strip()
    return baza_date.get(curatat, "Comanda nu a fost găsită în sistem.")


def intreaba_suport(prompt: str) -> str:
    client = genai.Client()
    modele = ["gemini-2.5-flash", "gemini-2.0-flash"]

    for model_name in modele:
        for incercare in range(3):
            try:
                # Conform ghidului oficial Google: client.chats.create
                chat = client.chats.create(
                    model=model_name,
                    config={
                        "tools": [cauta_status_comanda],
                    },
                )
                response = chat.send_message(prompt)
                return response.text
            except Exception as e:
                print(f"⚠️ [{model_name}] Încercarea {incercare + 1} a eșuat ({e})")
                time.sleep(1)
                continue

    return "Nu s-a putut genera un răspuns."


if __name__ == "__main__":
    prompt_client = "Salut! Unde este comanda mea #1042?"
    print(f"❓ Întrebare client: {prompt_client}\n")
    print("🤖 Se trimite la Gemini...\n")

    raspuns = intreaba_suport(prompt_client)
    print("--- RĂSPUNS FINAL DE LA AI ---")
    print(raspuns)