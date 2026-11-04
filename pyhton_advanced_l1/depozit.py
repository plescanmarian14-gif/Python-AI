from dataclasses import *
from enum import *

class Categorie(Enum):
    ELECTRONICE="electonice"
    IMBRACAMINTE="imbracaminte"
    ALIMENTE="alimente"

@dataclass
class Produs:
    id:int
    nume:str
    pret:float
    stoc:int
    categorie:Categorie

class Depozit:
    def __init__(self):
        self.produs:list[Produs]=[]
        self.next_id=1
    def adauga_produs(self, nume:str,pret:float,stoc:int,categorie:Categorie):
        produs_nou=Produs(
            id=self.next_id,
            nume=nume,
            pret=pret,
            stoc=stoc,
            categorie=categorie
        )
        self.produs.append(produs_nou)
        self.next_id+=1
        return produs_nou
    def get_produse_fara_stoc(self)->list[Produs]:
        return[produs for produs in self.produs if produs.stoc==0]

if __name__ == "__main__":
    depozit = Depozit()
    depozit.adauga_produs("Laptop", 3500.0, 5, Categorie.ELECTRONICE)
    depozit.adauga_produs("Tricou", 80.0, 0, Categorie.IMBRACAMINTE)  # Fără stoc!

    fara_stoc = depozit.get_produse_fara_stoc()
    print(f"Produse fără stoc: {len(fara_stoc)}")  # Trebuie să afișeze 1
    if fara_stoc:
        print(f"Nume produs fără stoc: {fara_stoc[0].nume}")