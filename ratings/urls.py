from django.urls import path
from .views import RatingCreateView

urlpatterns = [
    path('create/', RatingCreateView.as_view(), name='create-rating'),
]