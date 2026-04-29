from re import search

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .health_diary import HealthRecordRepository, date
from datetime import datetime


def old_home(request):
    return redirect('/')


def home(request):
    return HttpResponse(
        "<h2> Привіт, Django!</h2>"
        
        
        "<h1><strong> Щоденник самопочуття </strong></h1>"
    )


def index(request):
    http_method = request.method

    repo = HealthRecordRepository()
    user = repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")

    paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури")
    amlodipine = repo.add_medicine("Амлодипін", "5мг", "від тиску")

    record = repo.add_record(
        user_id=user.id,
        well_being="погано",
        temperature=37.8,
        pressure="130/80",
        complaints="Головний біль",
        comment="Прийняла ліки"
    )

    record.add_medicine(paracetamol)
    record.add_medicine(amlodipine)
    user_records = repo.get_user_records(user.id)

    return HttpResponse(f"""
        <h1>Щоденник самопочуття</h1>
        <h3>HTTP Method: {http_method}</h3>
        
        <p><strong>Користувач:</strong> {user}</p>
        <p><strong>Запис:</strong></p>
        <p>{record}</p>
        <p><strong>Записи за сьогодні:</strong> {len(user_records)}</p>
        <hr>
        <p>Django + HealthRecordRepository</p>
    """)


def records(request):
    http_method = request.method

    repo = HealthRecordRepository()
    user = repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")
    paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури")

    record1 = repo.add_record(
        user_id=user.id,
        well_being="дуже погано",
        temperature=38.6,
        pressure="120/80",
        complaints="Слабкість, температура",
        comment="(((("
    )
    record1.add_medicine(paracetamol)

    all_records = repo.get_user_records(user.id)

    records_html = ""
    for r in all_records:
        records_html += f"<p>{r}</p><hr>"

    return HttpResponse(f"""
        <h1>Всі записи про самопочуття</h1>
        <h3>Сторінка записів</h3>
        <p>HTTP Method: {http_method}</p>
        <h2>Записи користувача {user.username}:</h2>
        {records_html}
        
        <p><strong> Всього записів: </strong> {len(all_records)}</p>
        <hr>
    
    """)

def record_detail(request, record_id):
    repo = get_repo_with_data()

    for record in repo._records:
        if record.id == record_id:
            return HttpResponse(f"""
                <h1>Запис №{record_id}</h1>
                <p>{record}</p>
                
            """)
    raise Http404("Запис не знайдено")




def medicines(request):
    http_method = request.method
    search = request.GET.get('search', '')

    repo = HealthRecordRepository()

    paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури")
    amlodipine = repo.add_medicine("Амлодипін", "5мг", "від тиску")
    ibuprofen = repo.add_medicine("Ібупрофен", "200мг", "від болю")

    medicines_list = repo._medicines
    if search:
        medicines_list =  [m for m in medicines_list if search.lower() in m.name.lower()]

    medicines_html = ""
    for m in medicines_list:
        medicines_html += f"<p>{m}</p>"

    return HttpResponse(f"""
         <h1>Список ліків</h1>
         <p>HTTP Method: {http_method}</p>
         
         <form method="get">
            <input type="text" name="search" placeholder="Пошук..." value="{search}">
            
            <button type="submit">Шукати</button>
        </form>
         
         
         <h2>Доступні ліки: </h2>
         {medicines_html}
         
         <hr>
    """)


def profile(request):
    http_method = request.method

    repo = HealthRecordRepository()
    user = repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")

    return HttpResponse(f"""
        <h1>Профіль користувача</h1>
        <p>HTTP Method: {http_method}</p>
        
        <p><strong>Ім'я: </strong> {user.username} </p>
        <p><strong>Email: </strong> {user.email} </p>
        <p><strong>Роль: </strong> {user.role} </p>
        <p><strong>ID: </strong> {user.id} </p>
        
        <hr>
    """)


def administrator(request):
    return HttpResponse(
        "<hr><h1><strong> Привіт, АДМІН!</strong></h1><hr>"
    )


def create_test_data(repo: HealthRecordRepository):
    
    user = repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")
    
    
    paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури")
    amlodipine = repo.add_medicine("Амлодипін", "5мг", "від тиску")
    ibuprofen = repo.add_medicine("Ібупрофен", "200мг", "від болю")
    
    # Запис 1
    record1 = repo.add_record(
        user_id=user.id,
        well_being="погано",
        temperature=37.8,
        pressure="130/80",
        complaints="Головний біль",
        comment="Прийняла ліки"
    )
    record1.add_medicine(paracetamol)
    record1.add_medicine(amlodipine)
    
    # Запис 2
    record2 = repo.add_record(
        user_id=user.id,
        well_being="дуже погано",
        temperature=38.6,
        pressure="140/90",
        complaints="Сильна слабкість, кашель",
        comment="Звернулась до лікаря"
    )
    record2.add_medicine(paracetamol)
    record2.add_medicine(ibuprofen)
    
    # Запис 3
    record3 = repo.add_record(
        user_id=user.id,
        well_being="нормально",
        temperature=36.6,
        pressure="120/80",
        complaints="Втома",
        comment="Відпочинок допоміг"
    )
    
    return user


def get_repo_with_data():
    
    repo = HealthRecordRepository()
    create_test_data(repo)
    return repo