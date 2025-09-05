from django.db import models
from django.core.validators import MinValueValidator

class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)

class Room(models.Model):
    number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(max_length=50)
    price_cents = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    capacity = models.PositiveIntegerField(default=1)
    description = models.TextField(blank=True)
    amenities = models.ManyToManyField(Amenity, related_name="rooms", blank=True)

class Guest(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)

class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED"
        CANCELLED = "CANCELLED"
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="bookings")
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="bookings")
    check_in = models.DateField()
    check_out = models.DateField()  # exclusive
    total_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.CONFIRMED)
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"
        FAILED = "FAILED"
        REFUNDED = "REFUNDED"
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="payment")
    amount_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    provider_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
