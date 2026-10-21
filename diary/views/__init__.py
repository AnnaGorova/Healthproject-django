"""Public view handlers and helpers used by the existing URL configuration."""

from .access import (
    is_admin_or_superuser,
    get_accessible_patients,
    doctor_can_access_patient,
    is_doctor,
    is_admin,
)
from .slots import (
    is_slot_booked,
    get_available_slots,
    is_slot_available,
)
from .pages import (
    old_home,
    HomeView,
    AboutView,
    custom_404,
)
from .auth import (
    login_view,
    logout_view,
)
from .profiles import (
    profile,
    edit_profile,
    edit_doctor_profile,
)
from .records import (
    records,
    user_records,
    record_detail,
    create_record,
    my_records,
    edit_record,
    delete_record,
)
from .doctors import (
    doctor_dashboard,
    doctor_patients,
    users_list,
    doctors_list,
    patient_card,
)
from .appointments import (
    book_appointment,
    cancel_appointment,
    reschedule_appointment,
    filter_appointments,
    my_appointments,
    doctor_appointments,
    appointment_detail,
    doctor_cancel_appointment,
)
from .schedule import (
    manage_schedule,
    delete_schedule,
)
from .questions import (
    ask_question,
    my_questions,
    all_questions,
    answer_question,
    reply_question,
)
from .conclusions import (
    create_conclusion,
    view_conclusion,
    my_conclusions,
    icd10_autocomplete,
    edit_conclusion,
)
from .analytics import (
    health_analytics,
)
from .administration import (
    administrator,
    admin_user_create,
    admin_user_edit,
    admin_user_toggle,
)

__all__ = [
    "is_admin_or_superuser",
    "get_accessible_patients",
    "doctor_can_access_patient",
    "is_doctor",
    "is_admin",
    "is_slot_booked",
    "get_available_slots",
    "is_slot_available",
    "old_home",
    "HomeView",
    "AboutView",
    "custom_404",
    "login_view",
    "logout_view",
    "profile",
    "edit_profile",
    "edit_doctor_profile",
    "records",
    "user_records",
    "record_detail",
    "create_record",
    "my_records",
    "edit_record",
    "delete_record",
    "doctor_dashboard",
    "doctor_patients",
    "users_list",
    "doctors_list",
    "patient_card",
    "book_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    "filter_appointments",
    "my_appointments",
    "doctor_appointments",
    "appointment_detail",
    "doctor_cancel_appointment",
    "manage_schedule",
    "delete_schedule",
    "ask_question",
    "my_questions",
    "all_questions",
    "answer_question",
    "reply_question",
    "create_conclusion",
    "view_conclusion",
    "my_conclusions",
    "icd10_autocomplete",
    "edit_conclusion",
    "health_analytics",
    "administrator",
    "admin_user_create",
    "admin_user_edit",
    "admin_user_toggle",
]
