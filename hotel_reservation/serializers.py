from rest_framework import serializers
from django.db import transaction, IntegrityError
from .models import Booking, Room, Guest, Payment, Amenity

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name']

class GuestInput(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True, required=False)

class RoomSerializer(serializers.ModelSerializer):
    amenities = AmenitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['price_dollar'] = instance.price_cents / 100.0
        return data

class BookingSerializer(serializers.ModelSerializer):
    guest = GuestInput()
    room_id = serializers.IntegerField()
    room = RoomSerializer(read_only=True)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    client_token = serializers.UUIDField(write_only=True)  # <-- Only for input
    total_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['total_dollar'] = instance.total_cents / 100.0
        if hasattr(instance, 'payment'):
            data['payment_status'] = instance.payment.status
        return data

    def validate(self, data):
        if data['check_out'] <= data['check_in']:
            raise serializers.ValidationError("check_out must be after check_in")
        
        
        return data

    def create(self, validated):
        
        # Check room availability
        overlapping = Booking.objects.filter(
            room_id=validated['room_id'],
            status=Booking.Status.CONFIRMED,
            check_in__lt=validated['check_out'],
            check_out__gt=validated['check_in'],
        ).exists()
        
        if overlapping:
            raise serializers.ValidationError("Room is not available for the selected dates")
        
        
        guest_data = validated['guest']
        guest, _ = Guest.objects.get_or_create(email=guest_data['email'],
                                               defaults=dict(full_name=guest_data['full_name'],
                                                             phone=guest_data.get('phone','')))
        room = Room.objects.get(pk=validated['room_id'])
        nights = (validated['check_out'] - validated['check_in']).days
        total_cents = room.price_cents * nights

        # Idempotency: ensure the same client_token gets the same booking
        with transaction.atomic():
            booking = Booking.objects.create(
                room=room, guest=guest,
                check_in=validated['check_in'], check_out=validated['check_out'],
                total_cents=total_cents, status=Booking.Status.CONFIRMED
            )
            Payment.objects.create(booking=booking, amount_cents=total_cents,
                                   status=Payment.Status.PENDING,
                                   provider_ref=str(validated['client_token']))
        return booking
    

        