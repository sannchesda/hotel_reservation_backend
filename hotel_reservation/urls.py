from rest_framework.routers import DefaultRouter
from hotel_reservation.views import RoomViewSet, BookingViewSet  

router = DefaultRouter()
router.register(r'rooms', RoomViewSet)
router.register(r'bookings', BookingViewSet)  # <-- Register bookings

urlpatterns = router.urls