from fpdf import FPDF
from django.conf import settings
import os

def generate_appointment_pdf(appointment):
    pdf = FPDF()
    pdf.add_page()
    font_path_regular = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
    font_path_bold = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans-Bold.ttf")

    pdf.add_font("DejaVu", "", font_path_regular, uni=True)
    pdf.add_font("DejaVu", "B", font_path_bold, uni=True)


    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(200,10, "Упaт", ln = True, align = "C")
    pdf.ln(10)
    pdf.set_font("DejaVu", size=12)

    # Appointment details
    pdf.cell(0, 10, f"Пациент: {appointment.patient.first_name} {appointment.patient.last_name}", ln = True)
    pdf.cell(0, 10, f"Доктор: {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}", ln = True)
    pdf.cell(0, 10, f"Услуга: {appointment.service.name}", ln = True)
    pdf.cell(0, 10, f"Одделение: {appointment.department.name}", ln = True)
    pdf.cell(0, 10, f"Клиника: {appointment.hospital.name}", ln = True)
    pdf.cell(0, 10, f"Дата: {appointment.date}", ln = True)
    pdf.cell(0, 10, f"Време: {appointment.start_time} - {appointment.end_time}", ln = True)

    pdf_dir = os.path.join(settings.MEDIA_ROOT, "pdfs", "appointments")
    os.makedirs(pdf_dir, exist_ok = True)

    filename = f"appointment_{appointment.id}.pdf"
    filepath = os.path.join(pdf_dir, filename)
    pdf.output(filepath)

    return filepath

