from dataclasses import dataclass
from enum import Enum
import time
from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

# 1. Încărcăm cheia API din fișierul .env
load_dotenv()


# 2. Definim categoriile posibile
class Categorie(Enum):
    TEHNIC = "tehnic"
    FACTURARE = "facturare"
    GENERAL = "general"


# 3. Structura de date internă pentru un tichet
@dataclass
class Tichet:
    id: int
    client: str
    mesaj: str
    categorie: Categorie = Categorie.GENERAL


# 4. Noutatea din Ziua 3: Schema Pydantic pentru răspunsul JSON de la AI
class RaspunsSuportAI(BaseModel):
    categorie: Categorie
    urgenta: int = Field(description="Scor de la 1 (scăzută) la 5 (critică)")
    raspuns_client: str = Field(description="Răspuns amabil de 2-3 propoziții pentru client")


# 5. Clasa de management a tichetelor
class SuportManager:
    def __init__(self) -> None:
        self.tichete: list[Tichet] = []
        self.next_id: int = 1
        # Se inițializează clientul preluând automat GEMINI_API_KEY din mediu
        self.ai_client = genai.Client()

    def creaza_tichet(self, client: str, mesaj: str) -> Tichet:
        tichet_nou = Tichet(
            id=self.next_id,
            client=client,
            mesaj=mesaj
        )
        self.tichete.append(tichet_nou)
        self.next_id += 1
        return tichet_nou

    def analizeaza_si_raspunde(self, tichet_id: int) -> RaspunsSuportAI | None:
        tichet = next((t for t in self.tichete if t.id == tichet_id), None)
        if not tichet:
            print("Eroare: ID-ul tichetului este invalid.")
            return None

        prompt = (
            f"Analizează mesajul primit de la clientul {tichet.client}: '{tichet.mesaj}'.\n"
            f"Clasifică problema într-o categorie (TEHNIC, FACTURARE, GENERAL), "
            f"evaluează urgența (1-5) și redactează un răspuns amabil."
        )

        modele = ["gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash"]

        # Buclă de retry pe modele pentru gestionarea erorilor (ex. 503)
        for model_name in modele:
            for incercare in range(3):
                try:
                    response = self.ai_client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": RaspunsSuportAI,
                        },
                    )
                    # Parsăm JSON-ul direct în obiectul Pydantic
                    return RaspunsSuportAI.model_validate_json(response.text)
                except Exception as e:
                    print(f"⚠️ [{model_name}] Încercarea {incercare + 1} a eșuat ({e}). Reîncercăm...")
                    time.sleep(1)
                    continue

        print("Toate modelele sunt temporar ocupate.")
        return None


# 6. Execuția principală
if __name__ == "__main__":
    manager = SuportManager()

    # Creăm tichetul de la Elena
    t1 = manager.creaza_tichet(
        client="Elena",
        mesaj="Mi s-a retras de două ori suma de 50 RON de pe card pentru abonament!"
    )

    print("🤖 Se analizează tichetul și se generează răspunsul structurat JSON...\n")
    rezultat = manager.analizeaza_si_raspunde(t1.id)

    if rezultat:
        print("--- REZULTAT STRUCTURAT (PYDANTIC) ---")
        print(f"📂 Categorie detectată : {rezultat.categorie.value.upper()}")
        print(f"🚨 Nivel de Urgență   : {rezultat.urgenta}/5")
        print(f"💬 Răspuns AI Client  : {rezultat.raspuns_client}")