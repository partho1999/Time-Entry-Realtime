from django.urls import path
from .views import RunAIView, PersonCreateAPIView, PersonDetailAPIView, CameraCreateAPIView, CameraDetailAPIView

urlpatterns = [
    path('run/', RunAIView.as_view(), name='run_ai'),
    path('persons/', PersonCreateAPIView.as_view(), name='create-person'),
    path('person/<int:pk>/', PersonDetailAPIView.as_view(), name='person-detail'),
    path('cameras/', CameraCreateAPIView.as_view(), name='camera-list-create'),
    path('camera/<int:pk>/', CameraDetailAPIView.as_view(), name='camera-detail'),
]
