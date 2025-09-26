from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Rating
from appointments.models import Appointment
from .forms import RatingForm
from django.db.models import Avg, Count
from django.core.paginator import Paginator
from accounts.models import Doctor
from hospitals.models import Hospital 
from django.db.models import Q

def authentication_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/api/accounts/login/')  # Replace 'login' with your login URL name
        return view_func(request, *args, **kwargs)
    return wrapper

@authentication_required
def rate_doctor_hospital_page(request, appointment_id):

    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        patient=request.user,
        status='finished'  # Only allow rating for finished appointments
    )
    
    try:
        existing_rating = Rating.objects.get(
            appointment_id = appointment_id,
            doctor=appointment.doctor,
            hospital=appointment.hospital,
        )
    except Rating.DoesNotExist:
        existing_rating = None

    form = RatingForm(request.POST or None, instance=existing_rating)
    if request.method == 'POST':
        form = RatingForm(request.POST, instance=existing_rating)
        if form.is_valid():
            rating = form.save(commit=False)
            
            rating.doctor = appointment.doctor
            rating.hospital = appointment.hospital
            rating.is_anonymous = True  # Always anonymous
            rating.appointment_id = appointment_id
            rating.save()
            
            messages.success(request, "Вашата оценка е успешно зачувана. Ви благодариме!")
            appointment.is_rated = True
            appointment.save()
            return redirect('home')
        else:
            messages.error(request, "Ве молам поправете ги грешките во формата.")
    else:
        form = RatingForm(instance=existing_rating)
    context = {
        'form': form,
        'appointment': appointment,
    }
    
    return render(request, 'ratings/rate.html', context)

@authentication_required
def doctor_ratings(request):
    
    ratings = Rating.objects.filter(
        doctor=request.user.doctor
    ).select_related('hospital', 'doctor__user').order_by('-created_at')
    
    # Calculate statistics
    stats = ratings.aggregate(
        avg_rating=Avg('doctor_rating'),
        total_ratings=Count('id'),
        avg_hospital_rating=Avg('hospital_rating')
    )
    
    # Add pagination
    paginator = Paginator(ratings, 10)  # 10 ratings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ratings': page_obj,
        'stats': stats,
        'is_doctor_view': True,
    }
    
    return render(request, 'ratings/view_ratings.html', context)


@authentication_required
def hospital_ratings(request):
    
    ratings = Rating.objects.filter(
        hospital=request.user.hospital_admin.hospital
    ).select_related('doctor', 'doctor__user').order_by('-created_at')
    
    # Calculate statistics
    stats = ratings.aggregate(
        avg_rating=Avg('hospital_rating'),
        total_ratings=Count('id'),
        avg_doctor_rating=Avg('doctor_rating')
    )
    
    # Add pagination
    paginator = Paginator(ratings, 10)  # 10 ratings per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'ratings': page_obj,
        'stats': stats,
        'is_doctor_view': False,
    }
    
    return render(request, 'ratings/view_ratings.html', context)

@authentication_required
def search_ratings(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # Search for doctors
        doctors = Doctor.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(specialization__icontains=query)
        ).select_related('user').filter(authorized=True)
        
        # Search for hospitals
        hospitals = Hospital.objects.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(town__icontains=query)
        )
        
        # Format results
        for doctor in doctors:
            results.append({
                'type': 'doctor',
                'id': doctor.id,
                'name': f"Д-р {doctor.user.get_full_name()}",
                'specialization': doctor.specialization if hasattr(doctor, 'specialization') else 'Лекар',
                'hospital': doctor.hospital.name if doctor.hospital else 'Независен',
                'icon': 'bi-person-circle'
            })
        
        for hospital in hospitals:
            results.append({
                'type': 'hospital',
                'id': hospital.id,
                'name': hospital.name,
                'address': hospital.address,
                'town': hospital.town,
                'icon': 'bi-building'
            })
    
    context = {
        'query': query,
        'results': results,
        'results_count': len(results)
    }
    
    return render(request, 'ratings/search_ratings.html', context)

@authentication_required
def view_public_ratings(request, item_type, item_id):
    """View ratings for a specific doctor or hospital"""
    if item_type == 'doctor':
        doctor = get_object_or_404(Doctor, id=item_id, authorized=True)
        ratings = Rating.objects.filter(doctor=doctor).select_related('hospital').order_by('-created_at')
        
        # Calculate statistics
        stats = ratings.aggregate(
            avg_rating=Avg('doctor_rating'),
            total_ratings=Count('id'),
            avg_hospital_rating=Avg('hospital_rating')
        )
        
        context = {
            'ratings': ratings,
            'stats': stats,
            'profile': {
                'type': 'doctor',
                'name': f"Д-р {doctor.user.get_full_name()}",
                'specialization': doctor.specialization if hasattr(doctor, 'specialization') else 'Лекар',
                'hospital': doctor.hospital.name if doctor.hospital else 'Независен',
            }
        }
        
    elif item_type == 'hospital':
        hospital = get_object_or_404(Hospital, id=item_id)
        ratings = Rating.objects.filter(hospital=hospital).select_related('doctor', 'doctor__user').order_by('-created_at')
        
        # Calculate statistics
        stats = ratings.aggregate(
            avg_rating=Avg('hospital_rating'),
            total_ratings=Count('id'),
            avg_doctor_rating=Avg('doctor_rating')
        )
        
        context = {
            'ratings': ratings,
            'stats': stats,
            'profile': {
                'type': 'hospital',
                'name': hospital.name,
                'address': hospital.address,
                'town': hospital.town,
                'phone_number': hospital.phone_number
            }
        }
    
    else:
        return redirect('home')
    
    return render(request, 'ratings/public_ratings.html', context)

    