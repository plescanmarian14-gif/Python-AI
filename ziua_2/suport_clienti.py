from dataclasses import dataclass
from enum import Enum
from google import genai
from dotenv import load_dotenv
import time
load_dotenv()

class SuportManager:
    def __init__(self)->None:
        self.tichete=[]
        self.next_id=1
        self.ai_client=genai.Client()


class Categorie(Enum):
    TEHNIC = "tehnic"
    FACTURARE = "facturare"
    GENERAL = "general"


@dataclass
class Tichet:
    id: int
    client: str
    mesaj: str
    categorie: Categorie = Categorie.GENERAL


class SuportManager:
    def __init__(self) -> None:
        self.tichete: list[Tichet] = []
        self.next_id: int = 1
        self.ai_client=genai.Client()
    def creaza_tichet(self, client: str, mesaj: str) -> Tichet:
        tichet_nou = Tichet(
            id=self.next_id,
            client=client,
            mesaj=mesaj
        )
        self.tichete.append(tichet_nou)
        self.next_id += 1
        return tichet_nou

    def genereaza_raspuns_ai(self, tichet_id: int) -> str:
        # Căutăm tichetul corect în listă
        tichet = next((t for t in self.tichete if t.id == tichet_id), None)
        if not tichet:
            return "Eroare: ID-ul tichetului este invalid."

        # Construim promptul cu datele reale din tichet
        prompt = (
            f"Ești un agent amabil de la suport clienți. Creează un răspuns scurt "
            f"de 2-3 propoziții pentru clientul {tichet.client} care a trimis "
            f"acest mesaj: '{tichet.mesaj}'."
        )
        for incercare in range(1000):
            try:
                # Observă "models" la plural
                response = self.ai_client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                )
                return response.text
            except Exception as e:
                print(f"Eroare temporară API: {e}")
                time.sleep(1)
                continue
        return f"1000 de incercari"


if __name__ == "__main__":
    # 1. Instanțiem managerul
    manager = SuportManager()

    # 2. Creăm tichetul prin manager
    t1 = manager.creaza_tichet(
        client="Alex",
        mesaj="Aplicația se închide singură când deschid un fișier PDF."
    )

    print("🤖 Se generează răspunsul cu Gemini AI...\n")
    raspuns_ai = manager.genereaza_raspuns_ai(t1.id)
    print("--- RĂSPUNS DE LA SUPORT (AI) ---")
    print(raspuns_ai)