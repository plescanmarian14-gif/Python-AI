from dataclasses import dataclass
from enum import Enum
from google import genai


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Task:
    id: int
    titlu: str
    descriere: str
    prioritate: TaskPriority = TaskPriority.MEDIUM
    finalizat: bool = False


class TaskManager:
    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self._next_id: int = 1
        # Inițializăm clientul cu cheia ta
        self.ai_client = genai.Client(
            api_key="AQ.Ab8RN6Lp5NexCceemSiy-8a32MquKJ1pSuTB5-2pxFudqqJodA"
        )

    def adauga_task(
        self,
        titlu: str,
        descriere: str,
        prioritate: TaskPriority = TaskPriority.MEDIUM
    ) -> Task:
        task_nou = Task(
            id=self._next_id,
            titlu=titlu,
            descriere=descriere,
            prioritate=prioritate
        )
        self.tasks.append(task_nou)
        self._next_id += 1
        return task_nou

    def prioritizeaza_cu_ai(self, task_id: int) -> str:
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return "Task-ul nu a fost găsit."

        prompt = (
            f"Analizează acest task:\n"
            f"Titlu: {task.titlu}\n"
            f"Descriere: {task.descriere}\n\n"
            f"Recomandă o prioritate (LOW, MEDIUM sau HIGH) și oferă un motiv scurt de maxim 2 propoziții."
        )

        try:
            response = self.ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            return f"Eroare temporară API: {e}"


if __name__ == "__main__":
    manager = TaskManager()

    t1 = manager.adauga_task(
        titlu="Eroare critică în producție pe baza de date",
        descriere="Serverul de PostgreSQL nu mai răspunde și clienții nu pot face plăți."
    )

    print("🤖 Se trimite task-ul către Gemini API (gemini-3.8-flash)...\n")
    rezultat_ai = manager.prioritizeaza_cu_ai(t1.id)
    print("--- RĂSPUNS DE LA GEMINI ---")
    print(rezultat_ai)