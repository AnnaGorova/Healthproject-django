from typing import List
from datetime import datetime
from datetime import date




class User:

    def __init__(self, id: int, username: str,
                 email: str, role: str = "patient"):
        self.id = id
        self.username = username
        self.email = email
        self.role = role # patient, doctor, admin



    def __str__(self):
        if self.role == "doctor":
            return  f"Лікар: {self.username} ({self.email})"
        elif self.role == "admin":
            return  f"Адміністратор: {self.username} ({self.email})"
        else:
            return  f"Пацієнт: {self.username} ({self.email})"





class HealthRecord:

    def __init__(self, id: int, user_id: int, user: User, well_being="", temperature = 36.6,
                 pressure="", complaints="", comment=""):
        self.id = id
        self.user_id = user_id
        self.user = user
        self.date = datetime.now()
        self.well_being = well_being
        self.temperature = temperature
        self.pressure = pressure
        self.complaints = complaints
        self.comment = comment
        self.medicines = []

    def add_medicine(self, medicine: "Medicine"):
        self.medicines.append(medicine)

    def __str__(self):
        return f"Запис #{self.id} - {self.user.username} ({self.date:%d.%m.%Y})"




class Medicine:

    def __init__(self, id: int, name: str, dosage: str,
                 purpose: str = ""):
        self.id = id
        self.name = name
        self.dosage = dosage
        self.purpose = purpose #мета




    def __str__(self):
        return  (f"\n{self.name}  {self.dosage} - "
                 f"{self.purpose}")



class HealthRecordRepository:
    def __init__(self):
        self._records: List[HealthRecord] = []
        self._users: List[User] = []
        self._medicines: List[Medicine] = []
        self._next_record_id = 1
        self._next_user_id = 1
        self._next_medicine_id = 1

    def add_user(self, username: str, email: str, role: str= "patient"):
        user = User(self._next_user_id, username, email, role)
        self._users.append(user)
        self._next_user_id += 1
        return user

    def add_medicine(self, name: str, dosage: str, purpose: str= ""):
        medicine = Medicine(self._next_medicine_id, name,dosage,purpose)
        self._medicines.append(medicine)
        self._next_medicine_id += 1
        return medicine

    def add_record(self, user_id, **kwargs):
        user = self.find_user(user_id)
        if user is None:
            return None

        record = HealthRecord(self._next_record_id, user_id, user, **kwargs)
        self._records.append(record)
        self._next_record_id += 1
        return record


    def get_user_records(self, user_id: int):
        result = []
        for record in self._records:
            if record.user_id == user_id:
                result.append(record)
        return result

    def find_user(self, user_id):
        for user in self._users:
            if user.id == user_id:
                return user
        return None

    def get_all_users(self):
        return self._users.copy()
    
    def get_all_records(self):
        return self._records.copy()

    def get_all_medicines(self):
        return self._medicines.copy()

    def get_user(self, user_id: int):
        for user in self._users:
            if user.id == user_id:
                return user
        return None
    
    def get_record(self, record_id: int):
        for record in self._records:
            if record.id == record_id:
                return record
        return None

    def get_medicine(self, medicine_id: int):
        for medicine in self._medicines:
            if medicine.id == medicine_id:
                return medicine
        return None
    
    
    def get_users_count(self):
        return len(self._users)

    def get_records_count(self):
        return len(self._records)
    
    def get_medicines_count(self):
        return len(self._medicines)

    def get_records_by_date(self, target_date):
        result = []
        for record in self._records:
            if record.date.date() == target_date:
                result.append(record)
            
        return result
    
    def search_medicines_by_name(self, query: str):
       
        if not query:
            return self._medicines.copy()
        return [m for m in self._medicines if query.lower() in m.name.lower()]





if __name__ == "__main__": 

    print()
    print("Щоденник самопочуття")

    repo = HealthRecordRepository()

    user =  repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")

    paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури")
    amlodipine = repo.add_medicine("Амлодипін", "5мг", "від тиску")



    record = repo.add_record(
        user_id=user.id,
        well_being= "погано",
        temperature=37.8,
        pressure="130/80",
        complaints="Головний біль",
        comment="Прийняла ліки"
    )

    record.add_medicine(paracetamol)
    record.add_medicine(amlodipine)


    print(f"{record}")

    today = date.today()
    user_records = repo.get_user_records(user.id)
    print(f"\n Записи за сьогодні: {len(user_records)}")



















