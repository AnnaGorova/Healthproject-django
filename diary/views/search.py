from datetime import datetime
from functools import reduce
from operator import or_

from django.contrib.auth.decorators import login_required
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Appointment,
    HealthRecord,
    MedicalConclusion,
    Question,
    UserProfile,
)


def text_query(text, fields):
    """Шукає кожне введене слово хоча б в одному із заданих полів."""
    result = Q()
    for word in text.split():
        result &= reduce(or_, [
            Q(**{f"{field}__icontains": word}) for field in fields
        ])
    return result


def doctor_fields(prefix=""):
    """Поля імені, прізвища й по батькові лікаря."""
    return [
        f"{prefix}username", f"{prefix}middle_name",
        f"{prefix}user__first_name", f"{prefix}user__last_name",
    ]


def parse_search_date(text):
    """Розпізнає повну дату у звичних форматах."""
    for date_format in ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, date_format).date()
        except ValueError:
            continue
    return None


def display_date(value):
    """Форматує дату й час результату пошуку."""
    return timezone.localtime(value).strftime("%d.%m.%Y %H:%M")


def excerpt(text, length=90):
    """Скорочує довгий текст для випадаючого списку."""
    text = " ".join((text or "").split())
    return text if len(text) <= length else text[:length] + "…"


@login_required
def patient_search(request):
    """Єдиний пошук у кабінеті поточного пацієнта."""
    profile = getattr(request.user, "userprofile", None)
    if profile is None or profile.role != "patient" or request.user.is_superuser:
        result = JsonResponse({"results": []}, status=403)
        result["Cache-Control"] = "no-store"
        return result

    query = request.GET.get("q", "").strip()[:100]
    normalized = query.casefold()
    results = []

    def add_result(group, title, description, url):
        results.append({
            "group": group, "title": title,
            "description": description, "url": url,
        })

    def response():
        result = JsonResponse({"results": results})
        result["Cache-Control"] = "no-store"
        return result

    if len(query) < 2:
        return response()

    search_date = parse_search_date(query)
    sections = [
        ("Головна", "home", "головна кабінет"),
        ("Про нас", "about", "про нас система посібник"),
        ("Створити запис про самопочуття", "create_record",
         "створити додати запис показники самопочуття"),
        ("Мої записи про самопочуття", "my_records",
         "мої записи щоденник самопочуття"),
        ("Моя аналітика", "health_analytics", "аналітика графік динаміка показники"),
        ("Записатися до лікаря", "doctors_list",
         "лікарі записатися прийом спеціальність"),
        ("Мої записи до лікаря", "my_appointments", "мої прийоми записи до лікаря"),
        ("Мої висновки", "my_conclusions", "висновки діагноз призначення рекомендації"),
        ("Задати питання лікарю", "ask_question", "задати написати питання лікарю"),
        ("Мої питання", "my_questions", "питання відповіді повідомлення листування"),
        ("Профіль користувача", "profile", "профіль користувач особисті дані"),
    ]
    for title, route, keywords in sections:
        if all(word in keywords.casefold() for word in normalized.split()):
            add_result("Розділи", title, "Перейти до розділу", reverse(route))

    # Активні лікарі: ім’я, прізвище, спеціальність.
    doctors = UserProfile.objects.filter(
        role="doctor", user__is_active=True,
    ).filter(
        text_query(query, doctor_fields() + ["doctor_profile__specialty"])
    ).select_related("doctor_profile").order_by("username", "pk")[:5]

    for doctor in doctors:
        doctor_profile = getattr(doctor, "doctor_profile", None)
        specialty = doctor_profile.specialty if doctor_profile else "Спеціальність не вказана"
        add_result("Лікарі", doctor.username, specialty,
                   reverse("book_appointment", args=[doctor.id]))

    metrics = [
        ("temperature", ("температура",), "Температура", "°C"),
        ("heart_rate", ("пульс",), "Пульс", "уд/хв"),
        ("spo2", ("сатурація", "spo2", "spo₂"), "SpO₂", "%"),
        ("pressure_systolic", ("тиск", "артеріальний"), "Систолічний тиск", "мм рт. ст."),
        ("pressure_diastolic", ("тиск", "артеріальний"), "Діастолічний тиск", "мм рт. ст."),
        ("blood_sugar", ("глюкоза", "цукор"), "Глюкоза", "ммоль/л"),
        ("weight", ("вага",), "Вага", "кг"),
        ("sleep_hours", ("сон",), "Сон", "год"),
        ("steps", ("кроки",), "Кроки", ""),
        ("water_intake", ("вода",), "Вода", "мл"),
        ("calories", ("калорії",), "Калорії", "ккал"),
        ("energy_level", ("енергія",), "Енергія", "/ 10"),
        ("pain_level", ("біль",), "Біль", "/ 10"),
    ]
    record_filter = text_query(query, ["well_being", "mood", "complaints", "comment"])
    for value, label in HealthRecord._meta.get_field("mood").choices:
        if normalized in label.casefold():
            record_filter |= Q(mood=value)

    matched_metrics = [
        metric for metric in metrics
        if any(alias.startswith(normalized) for alias in metric[1])
    ]
    for field, aliases, label, unit in matched_metrics:
        record_filter |= Q(**{f"{field}__isnull": False})

    # Усі медичні результати обмежуємо власником перед пошуком.
    records = HealthRecord.objects.filter(user=profile, is_active=True)
    numeric_query = query.replace(",", ".")
    try:
        float(numeric_query)
        is_number = True
    except ValueError:
        is_number = False

    if is_number:
        records = records.annotate(**{
            f"search_{field}": Cast(field, output_field=CharField())
            for field, aliases, label, unit in metrics
        })
        for field, aliases, label, unit in metrics:
            record_filter |= Q(**{f"search_{field}__icontains": numeric_query})

    pressure_parts = query.split("/")
    if len(pressure_parts) == 2 and all(part.strip().isdigit() for part in pressure_parts):
        # Межі довжини захищають числовий фільтр від надмірно великих чисел.
        if all(len(part.strip()) <= 3 for part in pressure_parts):
            record_filter |= Q(
                pressure_systolic=int(pressure_parts[0]),
                pressure_diastolic=int(pressure_parts[1]),
            )

    if search_date:
        record_filter |= Q(date__date=search_date)

    for record in records.filter(record_filter).order_by("-date", "-pk")[:5]:
        values = []
        for field, aliases, label, unit in matched_metrics or metrics:
            value = getattr(record, field)
            if value is not None:
                values.append(f"{label}: {value} {unit}".strip())
        description = "; ".join(values) or record.complaints or record.well_being
        add_result(
            "Записи про самопочуття",
            f"Запис №{record.id} · {display_date(record.date)}",
            excerpt(description), reverse("record_detail", args=[record.id]),
        )

    # Власні прийоми.
    appointment_filter = text_query(
        query, doctor_fields("doctor__") + ["complaints", "comment"],
    )
    for value, label in Appointment.STATUS_CHOICES:
        if normalized in label.casefold():
            appointment_filter |= Q(status=value)
    if search_date:
        appointment_filter |= Q(date__date=search_date) | Q(created_at__date=search_date)

    appointments = Appointment.objects.filter(patient=profile).filter(
        appointment_filter,
    ).select_related("doctor", "cancelled_by").order_by("-date", "-pk")[:5]
    for appointment in appointments:
        add_result(
            "Прийоми", appointment.doctor.username,
            f"{display_date(appointment.date)} · {appointment.status_label}",
            reverse("my_appointments") + f"?status=all#appointment-{appointment.id}",
        )

    # Питання, відповіді та повідомлення у власних діалогах.
    question_filter = text_query(
        query, doctor_fields("doctor__") + ["question", "answer", "messages__text"],
    )
    for value, label in Question.STATUS_CHOICES:
        if normalized in label.casefold():
            question_filter |= Q(status=value)
    if search_date:
        question_filter |= Q(created_at__date=search_date)

    questions = Question.objects.filter(patient=profile).filter(
        question_filter,
    ).select_related("doctor").distinct().order_by("-created_at", "-pk")[:5]
    for question in questions:
        add_result(
            "Питання та листування", f"Питання до {question.doctor.username}",
            excerpt(question.question),
            reverse("my_questions") + f"#question-{question.id}",
        )

    # Висновок має належати пацієнту і бути пов’язаним із його прийомом.
    conclusion_filter = text_query(
        query, doctor_fields("doctor__") + [
            "diagnosis", "prescriptions", "recommendations", "icd10__code", "icd10__name",
        ],
    )
    if search_date:
        conclusion_filter |= Q(created_at__date=search_date)

    conclusions = MedicalConclusion.objects.filter(
        patient=profile, appointment__patient=profile,
    ).filter(conclusion_filter).select_related("doctor").order_by("-created_at", "-pk")[:5]
    for conclusion in conclusions:
        add_result(
            "Висновки", f"Висновок · {conclusion.doctor.username}",
            excerpt(conclusion.diagnosis),
            reverse("view_conclusion", args=[conclusion.appointment_id]),
        )

    return response()
