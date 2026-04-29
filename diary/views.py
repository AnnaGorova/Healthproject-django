from re import search

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .health_diary import HealthRecordRepository, date
from datetime import datetime


def old_home(request):
    return redirect('/')


def home(request):
    repo = get_repo_with_data()
    user = repo.find_user(1)
    records_count = len(repo.get_user_records(user.id))

    context = {
        'records_count': records_count,
        'user': user,
    }

    return render(request, 'diary/home.html', context)



def records(request):
    http_method = request.method

    repo = get_repo_with_data()

    user = repo.find_user(1)

    if user:
        all_records = repo.get_user_records(user.id)
    else:
        all_records = []

   
    records_html = ""
    for r in all_records:
        records_html += f"<p>ID-{r.id} - {r}</p><hr>"

    context = {
        'records': all_records,
        'user': user,
       
    }
    
    return render(request, 'diary/records.html', context)

def record_detail(request, pk):
    repo = get_repo_with_data()

    record = None
    for r in repo._records:
        if r.id == pk:
            record = r
            break
    

    if not record:
        raise Http404("Запис не знайдено")
    

    related_medicines = record.medicines
   
    
    context = {
        'record': record,
        'related_medicines': related_medicines,  
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)



def medicines(request):
    http_method = request.method
    search = request.GET.get('search', '')

    repo = get_repo_with_data()

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
        complaints="Головний біль, температура 38.5, слабкість " \
        "у всьому тілі, кашель, нежить, біль у горлі, запаморочення",
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
        complaints="Легке запаморочення при зміні положення тіла, шум у вухах, невелика слабкість у ногах, " \
        "головний біль помірний в потиличній ділянці",
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