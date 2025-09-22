from django import forms
from .models import Rating

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['doctor_rating', 'hospital_rating', 'comment', 'is_anonymous']
        widgets = {
            'doctor_rating': forms.RadioSelect(choices=[(i, f'{i} star{"s" if i != 1 else ""}') for i in range(1, 6)]),
            'hospital_rating': forms.RadioSelect(choices=[(i, f'{i} star{"s" if i != 1 else ""}') for i in range(1, 6)]),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Вашиот коментар (опционално)...'}),
            'is_anonymous': forms.HiddenInput(),  # Always anonymous as requested
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_anonymous'].initial = True  # Force anonymous