from django.shortcuts import render
from django.db.models import Exists, OuterRef, Q
from .models import Room, Booking
from django.http import JsonResponse
from .serializers import RoomSerializer, BookingSerializer
from rest_framework import viewsets

def health_check(request):
    return JsonResponse({"status": "ok"})

def available_rooms_qs(check_in, check_out, max_price=None, amenity_names=None):
    overlap = Exists(
        Booking.objects.filter(
            room=OuterRef('pk'),
            status=Booking.Status.CONFIRMED,
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
    )
    qs = Room.objects.annotate(has_overlap=overlap).filter(has_overlap=False)
    if max_price is not None:
        qs = qs.filter(price_cents__lte=max_price)
    if amenity_names:
        qs = qs.filter(amenities__name__in=amenity_names).distinct()
    return qs

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer