from dataclasses import dataclass
from enum import Enum

class TaskPriority(Enum):
    LOW="low"
    MEDIUM="medium"
    HIGH="high"

@dataclass
class Task:
    id:int
    titlu:str
    descriere:str
    prioritate:TaskPriority=TaskPriority.MEDIUM
    finalizat:bool=False

class TaskManager:
    def __init__(self)->None:
        self.tasks:list[Task]=[]
        self._next_id:int=1
    def adauga_task(self,titlu:str,descriere:str,prioritate:TaskPriority=TaskPriority.MEDIUM)->Task:
        task_nou=Task(
            id=self._next_id,
            titlu=titlu,
            descriere=descriere,
            prioritate=prioritate
        )
        self.tasks.append(task_nou)
        self._next_id+=1
        return task_nou
    def finalizeaza_task(self,task_id:int)->bool:
        for task in self.tasks:
            if task.id==task_id:
                task.finalizat=True
                return True
        return False
    def get_taskuri_active(self)->list[Task]:
        return [task for task in self.task if not task.finalizat]

if __name__ == "__main__":
    manager = TaskManager()

    # Adaugam 2 task-uri
    t1 = manager.adauga_task(
        titlu="Configurare mediu Python",
        descriere="Instalat pydantic si google-genai",
        prioritate=TaskPriority.HIGH
    )
    t2 = manager.adauga_task(
        titlu="Invatat Enum si Dataclass",
        descriere="Scris primul script OOP cu Type Hints"
    )

    print(f" Total task-uri create: {len(manager.tasks)}")
    print(f" Task 1 detaliat: {t1}\n")

    # Finalizam primul task
    manager.finalizeaza_task(t1.id)
    print(f" Task-ul {t1.id} a fost finalizat!")

    # Verificam cate au ramas active
    active = manager.get_taskuri_active()
    print(f" Task-uri active ramase: {len(active)}")
    print(f" Task-ul ramas active: {active[0].titlu}")