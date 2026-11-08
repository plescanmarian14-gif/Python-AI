import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Încărcăm fișierul .env din folderul curent
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


def converteste_valuta(suma: float, din: str, in_valuta: str) -> str:
    """Convertește o sumă de bani dintr-o valută în alta.

    Args:
        suma: Suma de bani de convertit (ex: 50).
        din: Moneda de origine (ex: EUR, USD, RON).
        in_valuta: Moneda de destinație (ex: RON, EUR, USD).
    """
    baza_de_date = {("EUR", "RON"): 5.0, ("USD", "RON"): 4.9}
    cheie = (din.upper(), in_valuta.upper())
    daca_exista = baza_de_date.get(cheie)
    if daca_exista:
        rez = suma * daca_exista
        return f"{suma} {din} înseamnă aproximativ {rez:.2f} {in_valuta}"
    return f"Cursul între {din} și {in_valuta} este indisponibil."


# 1. Inițializăm clientul
client = genai.Client()

# 2. Creăm sesiunea de chat cu funcția pasată în tools
chat = client.chats.create(
    model="gemini-3.8-flash",
    config={
        "tools": [converteste_valuta],
    },
)

# 3. Trimitem întrebarea
intrebare = "Cât înseamnă 50 EUR în RON?"
print(f"👤 Întrebare: {intrebare}\n")

# ✅ Corectat: send_message (fără punct în mijloc)
raspuns = chat.send_message(intrebare)

print("🤖 Răspuns de la Gemini:")
print(raspuns.text)