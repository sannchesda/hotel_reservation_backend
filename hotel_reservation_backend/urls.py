
from django.contrib import admin
from django.urls import path, include
from hotel_reservation.views import health_check, RoomViewSet, welcome

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', health_check, name='health'),  # Added health check endpoint
    path('', welcome, name='welcome'),  # Added health check endpoint
    path('api/', include('hotel_reservation.urls')),  # Include the app's API URLs
]
