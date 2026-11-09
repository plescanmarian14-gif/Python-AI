from dotenv import load_dotenv
import time
from pathlib import Path
from google import genai

env_path=Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

def afla_vremea(oras:str)->str:
    baza_de_date={
        "pascani":"20 grade",
        "iasi":"21 grade"
    }
    curat=oras.lower().strip()
    return baza_de_date.get(curat,f"{oras} are aproximativ 19 grade")

def converteste_valuta(suma:float,din:str,in_valuta:str)->str:
    baza_de_data={
        ("EUR","RON"):5.2,
        ("USD","RON"):4.9
    }
    cheie=(din.upper().strip(),in_valuta.upper().strip())
    curs=baza_de_data.get(cheie)
    if curs:
        rez=suma*curs
        return f"{suma}{din} inseamna {rez:.2f} {in_valuta}"
    return f"curs indisponibil"

def intreaba_suport()->str:
    client=genai.Client()
    chat=client.chats.create(
        model="gemini-3.8-flash",
        config={
            "tools":[afla_vremea,converteste_valuta],
        },
    )
    print("Scrie iesi sau exit pentru a opri")
    while True:
        utilizator=input("\n Tu: ").strip()
        if not utilizator:
            continue
        if utilizator.lower() in ["iesi","exit"]:
            print("Good bye!!")
            break
        for incercare in range(3):
            try:
                response=chat.send_message(utilizator)
                print(f"{response.text}")
                break
            except Exception as e:
                print(f"Avem eroarea: {e}")
                time.sleep(1)

if __name__=="__main__":
    intreaba_suport()
