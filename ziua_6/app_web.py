import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Încărcare mediu & cheie API
env_local = Path(__file__).resolve().parent / ".env"
env_parent = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_local)
load_dotenv(dotenv_path=env_parent)
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(page_title="Asistent AI Meteo si Valuta", page_icon="🤖")
st.title("🤖 Asistent Interactiv Gemini")

if not api_key:
    st.error("❌ Nu s-a găsit cheia GEMINI_API_KEY în fișierul .env!")
    st.stop()

# Initializam clientul direct
client = genai.Client(api_key=api_key)


# 2. DEFINIRE FUNCȚII (TOOLS)
def afla_vremea(oras: str) -> str:
    """Află starea vremii și temperatura dintr-un oraș specific.
    Args:
        oras: Numele orașului (ex: Pașcani, Iași, București).
    """
    baza_vreme = {
        "pascani": "20°C și senin",
        "iasi": "21°C și parțial noros",
        "bucuresti": "25°C și soare",
    }
    curat = oras.lower().strip()
    # Eliminam diacriticele automat
    for vechi, nou in [("ș", "s"), ("ț", "t"), ("ă", "a"), ("â", "a"), ("î", "i")]:
        curat = curat.replace(vechi, nou)

    res = baza_vreme.get(curat, f"19°C (estimat în {oras})")
    return f"Vremea în {oras}: {res}"


def converteste_valuta(suma: float, din: str, in_valuta: str) -> str:
    """Convertește o sumă de bani dintr-o valută în alta.
    Args:
        suma: Suma numerică (ex: 50, 100).
        din: Moneda sursă (ex: EUR, USD).
        in_valuta: Moneda țintă (ex: RON).
    """
    cursuri = {("EUR", "RON"): 5.2, ("USD", "RON"): 4.9, ("EUR", "USD"): 1.08}
    cheie = (din.upper().strip(), in_valuta.upper().strip())
    curs = cursuri.get(cheie)
    if curs:
        rez = suma * curs
        return f"{suma} {din} înseamnă {rez:.2f} {in_valuta}."
    return f"Curs indisponibil între {din} și {in_valuta}."


# Dicționar local pentru apelul direct
FUNCTII_DISPONIBILE = {
    "afla_vremea": afla_vremea,
    "converteste_valuta": converteste_valuta,
}

# 3. ISTORIC MESAJE
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    if st.button("🔄 Resetează Chat"):
        st.session_state.messages = []
        st.rerun()

# Afișare mesaje anterioare
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 4. CASUȚĂ DE CHAT & LOGICĂ DIRECTĂ
if prompt := st.chat_input("Scrie întrebarea ta aici (ex: vreme iasi)..."):
    # Adăugăm mesajul utilizatorului
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Procesez cererea..."):
            try:
                # 1. Pasul cerere inițială către Gemini
                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        tools=[afla_vremea, converteste_valuta],
                    ),
                )

                # 2. Verificăm dacă Gemini solicită rularea unei funcții
                if response.function_calls:
                    for call in response.function_calls:
                        nume = call.name
                        args = call.args

                        if nume in FUNCTII_DISPONIBILE:
                            # Executăm funcția Python local direct!
                            rezultat_functie = FUNCTII_DISPONIBILE[nume](**args)

                            # Trimitem rezultatul înapoi la Gemini pentru a-l pune în frază
                            r_final = client.models.generate_content(
                                model="gemini-3.8-flash",
                                contents=f"Utilizatorul a întrebat: '{prompt}'. Rezultatul executării funcției {nume} este: {rezultat_functie}. Răspunde-i scurt și clar utilizatorului.",
                            )
                            text_raspuns = r_final.text
                        else:
                            text_raspuns = f"Eroare: Funcția {nume} nu există."
                else:
                    text_raspuns = response.text if response.text else "Nu am putut genera un răspuns."

                # Afișăm și salvăm răspunsul final
                st.markdown(text_raspuns)
                st.session_state.messages.append({"role": "assistant", "content": text_raspuns})

            except Exception as e:
                st.error(f"⚠️ Eroare: {e}")