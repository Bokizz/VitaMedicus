from fpdf import FPDF
from django.conf import settings
import os

def generate_appointment_pdf(appointment):
    pdf = FPDF()
    pdf.add_page()
    font_path_regular = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
    font_path_bold = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans-Bold.ttf")
    logo_img_path = os.path.join(settings.BASE_DIR, "static", "images", "vitamedicus2.png")

    pdf.add_font("DejaVu", "", font_path_regular, uni=True)
    pdf.add_font("DejaVu", "B", font_path_bold, uni=True)

    # Header
    pdf.set_font("DejaVu", "B", 18)
    pdf.image(logo_img_path, x = 10, y = 8, w = 30, h = 0)
    pdf.ln(25)
    
    # --- Title ---
    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "Упат за закажан преглед", ln=True, align="C")
    pdf.ln(8)

    # --- Intro text ---
    pdf.set_font("DejaVu", size=12)
    intro_text = (
        "Овој документ претставува официјална потврда за закажан преглед преку "
        "платформата ВитаМедикус. Ве молиме да го зачувате и презентирате при пристигнување "
        "во клиниката."
    )
    pdf.multi_cell(0, 8, intro_text)
    pdf.ln(5)

    # --- Appointment details ---
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Детали за закажувањето:", ln=True)
    pdf.ln(3)

    pdf.set_font("DejaVu", size=12)
    pdf.cell(0, 8, f"Пациент: {appointment.patient.first_name} {appointment.patient.last_name}", ln=True)
    pdf.cell(0, 8, f"Доктор: {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}", ln=True)
    pdf.cell(0, 8, f"Услуга: {appointment.service.name}", ln=True)
    pdf.cell(0, 8, f"Одделение: {appointment.department.name}", ln=True)
    pdf.cell(0, 8, f"Клиника: {appointment.hospital.name}", ln=True)
    pdf.cell(0, 8, f"Дата: {appointment.date}", ln=True)
    pdf.cell(0, 8, f"Време: {appointment.start_time} - {appointment.end_time}", ln=True)

    pdf.ln(10)

    # --- Additional instructions ---
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, "Инструкции за пациентот:", ln=True)
    pdf.set_font("DejaVu", size=12)
    instructions = (
        "- Ве молиме пристигнете најмалку 15 минути пред закажаниот термин.\n"
        "- Понесете ги со вас сите потребни медицински документи.\n"
        "- За дополнителни прашања обратете се на рецепцијата на клиниката."
    )
    pdf.multi_cell(0, 8, instructions)

    # --- Footer ---
    pdf.ln(15)
    pdf.set_font("DejaVu", size=10)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(
        0,
        6,
        "Овој документ е генериран автоматски преку системот на ВитаМедикус.\n"
        "За повеќе информации посетете ја нашата веб страна или контактирајте корисничка поддршка."
    )

    pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", "appointments")
    os.makedirs(pdf_dir, exist_ok = True)

    filename = f"appointment_{appointment.id}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    pdf.output(filepath)

    return filepath

