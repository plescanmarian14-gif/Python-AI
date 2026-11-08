import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()


def afla_vremea(oras:str) -> str:
    baza_de_date={
        "bucuresti":"20 grade",
        "iasi":"21 grade",
        "pascani":"19 grade"
    }
    curat=oras.lower().strip()
    return baza_de_date.get(curat,f"Temperatura in {oras} este de 19 grade(valoarea estimata) ")


def intreaba_suport(prompt:str)->str:
    client=genai.Client()
    modele=["gemini-2.5-flash", "gemini-2.0-flash"]
    for model1 in modele:
        for incercari in range(3):
            try:
                chat=client.chats.create(
                    model=model1,
                    config={"tools":[afla_vremea],},
                )
                response=chat.send_message(prompt)
                return response.text
            except Exception as e:
                print(f"{model1} incercare{incercari+1} cu eroarea({e})")
                time.sleep(1)
                continue
    return "Nu s-a putut gasi"

if __name__ == "__main__":
    prompt_test = "Cum este vremea în Iași azi?"
    print(f"👤 Întrebare: {prompt_test}\n")

    raspuns = intreaba_suport(prompt_test)
    print("🤖 Răspuns de la Gemini:")
    print(raspuns)