# VitaMedicus – Web Health Care Application

VitaMedicus is a full-stack healthcare web application designed to manage hospitals, doctors, patients, and medical appointments. The system provides role-based access control, appointment scheduling with conflict detection, and rating functionality for healthcare providers.

---

## Features

- User registration and authentication for patients, doctors, and administrators  
- Role-based authorization and secure access control  
- Appointment scheduling with availability and conflict checking  
- Hospital, department, and service management  
- Doctor and hospital rating system  
- Appointment status tracking (pending, accepted, rejected)  
- PDF generation for appointment confirmations and visit summaries  
- Blacklisting and abuse monitoring for excessive appointment misuse  
- RESTful API endpoints for core application functionality  

---

## Tech Stack

- **Backend:** Django, Django REST Framework  
- **Database:** SQLite (development)  
- **Authentication:** Django Authentication System  
- **PDF Generation:** ReportLab  
- **Data Handling:** Django ORM  

---

## Project Structure
VitaMedicus/
├── accounts/ # User management and authentication
├── hospitals/ # Hospital and department logic
├── appointments/ # Appointment scheduling and status handling
├── ratings/ # Rating and review system
├── api/ # REST API endpoints
├── templates/ # HTML templates
├── static/ # Static files
└── manage.py


---

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/Bokizz/VitaMedicus.git
cd VitaMedicus
```
2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Apply database migrations:
```bash
python manage.py migrate
```
5. Run the development server:
```bash
python manage.py runserver
```
6. Open in browser:
```bash
http://127.0.0.1:8000/
```
