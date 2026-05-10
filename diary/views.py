from re import search

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from .health_diary import HealthRecordRepository, date
from datetime import datetime
from .models import UserProfile, HealthRecord, Medicine
from django.shortcuts import get_object_or_404

def old_home(request):
    return redirect('/')


def home(request):
    user = UserProfile.objects.filter(id=1).first()
    records_count = HealthRecord.objects.filter(user=user).count() if user else 0

    context = {
        'records_count': records_count,
        'user': user,
    }

    return render(request, 'diary/home.html', context)



def records(request):
    http_method = request.method


    user = UserProfile.objects.get(id=1)
    all_records = HealthRecord.objects.filter(user=user)
       
    context = {
        'records': all_records,
        'user': user,
       
    }
    
    return render(request, 'diary/records.html', context)

def user_records(request, user_id):
    user = get_object_or_404(UserProfile, id=user_id)
    all_records = HealthRecord.objects.filter(user=user)

    context = {
        'records': all_records,
        'user': user,
    }

    return render(request, 'diary/records.html', context)

def record_detail(request, pk):
    record = get_object_or_404(HealthRecord, id=pk)
           
    
    context = {
        'record': record,
        'related_medicines': record.medicines.all(),  
        'record_date': record.date
    }

    return render(request, 'diary/record_detail.html', context)



def medicines(request):
    http_method = request.method
    search = request.GET.get('search', '')
    
    if search:
        medicines_list = Medicine.objects.filter(name__icontains=search)
    else:
        medicines_list = Medicine.objects.all()
   
    context = {
        'medicines': medicines_list,
        'search_query': search,
        'http_method': http_method,
    }
      
    return render(request, 'diary/medicines.html', context)
 


def profile(request):
    http_method = request.method

    user = UserProfile.objects.filter(id=1).first()
    if not user:
        user = UserProfile.objects.create(
            username="Olga Ivanova", 
            email="olga_I@gmail.com", 
            role="patient") 
    
    context = {
        'user': user,
        'http_method': http_method,
    }
    return render(request, 'diary/profile.html', context)
   
def users_list(request):
    users = UserProfile.objects.all()

    context = {
        'users': users,
        'users_count': users.count(),
    }
    
    return render(request, 'diary/users_list.html', context)     




def administrator(request):
    return render(request, 'diary/administrator.html')


# def create_test_data(repo: HealthRecordRepository):
    
#     user1 = repo.add_user("Olga Ivanova", "olga_I@gmail.com", "patient")
#     user2 = repo.add_user("Petro Shevchenko", "petro@gmail.com", "patient")
#     user3 = repo.add_user("Anna Kovalenko", "anna.kovalenko@gmail.com", "patient")
#     user4 = repo.add_user("Dr. Oksana Bondarenko", "dr.bondarenko@clinic.com", "doctor")
#     user5 = repo.add_user("Admin", "admin@health.com", "admin")
#     user6 = repo.add_user("Mykhailo Tkachenko", "misha.tkachenko@gmail.com", "patient")
#     user7 = repo.add_user("Iryna Petrenko", "iryna.petrenko@gmail.com", "patient")
#     user8 = repo.add_user("Dr. Andriy Melnyk", "dr.melnyk@clinic.com", "doctor")
#     user9 = repo.add_user("Kateryna Shevchenko", "kateryna@gmail.com", "patient")
#     user10 = repo.add_user("Volodymyr Koval", "volodymyr.koval@gmail.com", "patient")
    
#     # Ліки
#     paracetamol = repo.add_medicine("Парацетамол", "500мг", "від температури та болю")
#     amlodipine = repo.add_medicine("Амлодипін", "5мг", "від підвищеного тиску")
#     ibuprofen = repo.add_medicine("Ібупрофен", "200мг", "від болю та запалення")
#     noshpa = repo.add_medicine("Но-шпа", "40мг", "спазмолітик, від болю в животі")
#     aspirin = repo.add_medicine("Аспірин", "100мг", "розрідження крові, від головного болю")
#     loratadine = repo.add_medicine("Лоратадин", "10мг", "від алергії")
#     omeprazole = repo.add_medicine("Омепразол", "20мг", "від печії та болю в шлунку")
#     bisoprolol = repo.add_medicine("Бісопролол", "2.5мг", "зниження тиску, серцебиття")
#     ambroxol = repo.add_medicine("Амброксол", "30мг", "від кашлю та мокротиння")
#     vitamin_c = repo.add_medicine("Вітамін С", "500мг", "імунітет, застуда")
#     magnesium = repo.add_medicine("Магній B6", "300мг", "від судом та стресу")
#     melatonin = repo.add_medicine("Мелатонін", "3мг", "покращення сну")
    
#     # Запис 1
#     record1 = repo.add_record(
#         user_id=user1.id,
#         well_being="погано",
#         temperature=37.8,
#         pressure="130/80",
#         complaints="Головний біль, температура 38.5, слабкість у всьому тілі, кашель, нежить, біль у горлі, запаморочення",
#         comment="Прийняла ліки"
#     )
#     record1.add_medicine(paracetamol)
#     record1.add_medicine(amlodipine)
    
#     # Запис 2
#     record2 = repo.add_record(
#         user_id=user1.id,  
#         well_being="дуже погано",
#         temperature=38.6,
#         pressure="140/90",
#         complaints="Легке запаморочення при зміні положення тіла, шум у вухах, невелика слабкість у ногах, головний біль помірний в потиличній ділянці",
#         comment="Звернулась до лікаря"
#     )
#     record2.add_medicine(paracetamol)
#     record2.add_medicine(ibuprofen)
    
#     # Запис 3
#     record3 = repo.add_record(
#         user_id=user1.id,  
#         well_being="нормально",
#         temperature=36.6,
#         pressure="120/80",
#         complaints="Втома",
#         comment="Відпочинок допоміг"
#     )
    
#     # Запис 4 - алергія
#     record4 = repo.add_record(
#         user_id=user1.id, 
#         well_being="задовільно",
#         temperature=36.8,
#         pressure="115/75",
#         complaints="Нежить, чхання, свербіж в очах, сльозотеча, закладеність носа, першіння в горлі",
#         comment="Почався сезон цвітіння"
#     )
#     record4.add_medicine(loratadine)
    
#     # Запис 5 - проблеми зі шлунком
#     record5 = repo.add_record(
#         user_id=user1.id,  
#         well_being="погано",
#         temperature=36.5,
#         pressure="110/70",
#         complaints="Печія після їжі, біль в епігастральній ділянці, відчуття важкості, кислий присмак у роті",
#         comment="Переїла гострої їжі"
#     )
#     record5.add_medicine(omeprazole)
#     record5.add_medicine(noshpa)
    
#     # Запис 6 - застуда
#     record6 = repo.add_record(
#         user_id=user1.id,  
#         well_being="погано",
#         temperature=38.2,
#         pressure="125/80",
#         complaints="Нежить, кашель з мокротинням, біль у горлі, головний біль, озноб",
#         comment="Захворіла на ГРВІ"
#     )
#     record6.add_medicine(paracetamol)
#     record6.add_medicine(ambroxol)
#     record6.add_medicine(vitamin_c)
    
#     # Запис 7 - серцебиття та тиск
#     record7 = repo.add_record(
#         user_id=user1.id,  
#         well_being="нормально",
#         temperature=36.6,
#         pressure="145/95",
#         complaints="Прискорене серцебиття, відчуття тривоги, пульсація в скронях, легке запаморочення",
#         comment="Стрес на роботі"
#     )
#     record7.add_medicine(bisoprolol)
#     record7.add_medicine(amlodipine)
    
#     # Запис 8 - судоми та стрес
#     record8 = repo.add_record(
#         user_id=user1.id,  
#         well_being="задовільно",
#         temperature=36.4,
#         pressure="120/78",
#         complaints="Судоми в литкових м'язах вночі, м'язова напруга, поганий сон, дратівливість",
#         comment="Перенапруження"
#     )
#     record8.add_medicine(magnesium)
#     record8.add_medicine(melatonin)
    
#     # Запис 9 - головний біль та тиск
#     record9 = repo.add_record(
#         user_id=user1.id,  
#         well_being="погано",
#         temperature=36.7,
#         pressure="150/95",
#         complaints="Сильний головний біль в потилиці, шум у вухах, мушки перед очима, нудота",
#         comment="Гіпертонічний криз"
#     )
#     record9.add_medicine(amlodipine)
#     record9.add_medicine(bisoprolol)
    
#     # Запис 10 - біль у спині
#     record10 = repo.add_record(
#         user_id=user1.id, 
#         well_being="задовільно",
#         temperature=36.5,
#         pressure="118/72",
#         complaints="Біль у попереку після фізичного навантаження, скутість рухів, біль при нахилах",
#         comment="Перетренувалась у спортзалі"
#     )
#     record10.add_medicine(ibuprofen)
    
#     # Запис 11 - безсоння
#     record11 = repo.add_record(
#         user_id=user1.id,  
#         well_being="нормально",
#         temperature=36.4,
#         pressure="115/70",
#         complaints="Труднощі із засинанням, часті пробудження вночі, раннє пробудження, відчуття невиспаності",
#         comment="Безсоння через стрес"
#     )
#     record11.add_medicine(magnesium)
#     record11.add_medicine(melatonin)
    
#     # Запис 12 - кашель та застуда
#     record12 = repo.add_record(
#         user_id=user1.id,  
#         well_being="погано",
#         temperature=37.5,
#         pressure="128/82",
#         complaints="Сухий нападоподібний кашель, першіння в горлі, біль за грудиною, осиплість голосу",
#         comment="Застуда після переохолодження"
#     )
#     record12.add_medicine(ambroxol)
#     record12.add_medicine(vitamin_c)
    
#     # Запис 13 - спазми в животі
#     record13 = repo.add_record(
#         user_id=user1.id,  
#         well_being="погано",
#         temperature=36.9,
#         pressure="122/78",
#         complaints="Переймоподібний біль в нижній частині живота, здуття, нудота, відсутність апетиту",
#         comment="Харчове отруєння"
#     )
#     record13.add_medicine(noshpa)
    
#     # Запис 14 - мігрень
#     record14 = repo.add_record(
#         user_id=user1.id,  
#         well_being="дуже погано",
#         temperature=36.5,
#         pressure="130/85",
#         complaints="Пульсуючий односторонній головний біль, світлобоязнь, нудота, блювання, аура перед нападом",
#         comment="Напад мігрені"
#     )
#     record14.add_medicine(paracetamol)
#     record14.add_medicine(magnesium)
    
#     return user1 


# def get_repo_with_data():
    
#     repo = HealthRecordRepository()
#     create_test_data(repo)
#     return repo