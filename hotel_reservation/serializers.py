from rest_framework import serializers
from django.db import transaction, IntegrityError
from .models import Booking, Room, Guest, Payment

class GuestInput(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField(allow_blank=True, required=False)

class RoomSerializer(serializers.ModelSerializer):
    
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
    client_token = serializers.UUIDField(write_only=True, required=False)  # <-- Only required for creation
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
        # Only validate date ordering if both dates are provided
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        
        # For updates, get the current instance dates if not provided
        if self.instance:
            check_in = check_in or self.instance.check_in
            check_out = check_out or self.instance.check_out
        
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in")
        
        # Require client_token for creation (when instance doesn't exist)
        if not self.instance and 'client_token' not in data:
            raise serializers.ValidationError("client_token is required for new bookings")
        
        # Check for overlapping bookings during creation
        if not self.instance and 'room_id' in data and check_in and check_out:
            # First check if this is an idempotent request (same client_token already exists)
            client_token_str = str(data['client_token'])
            existing_payment = Payment.objects.filter(provider_ref=client_token_str).first()
            
            # If client_token already exists, skip overlap validation (idempotency)
            if not existing_payment:
                overlapping = Booking.objects.filter(
                    room_id=data['room_id'],
                    status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                    check_in__lt=check_out,
                    check_out__gt=check_in,
                ).exists()
                
                if overlapping:
                    raise serializers.ValidationError("Room is not available for the selected dates")
        
        # Check for overlapping bookings during updates
        elif self.instance and ('room_id' in data or 'check_in' in data or 'check_out' in data):
            room_id = data.get('room_id', self.instance.room_id)
            
            overlapping = Booking.objects.filter(
                room_id=room_id,
                status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).exclude(pk=self.instance.pk).exists()
            
            if overlapping:
                raise serializers.ValidationError("Room is not available for the selected dates")
        
        return data

    def create(self, validated):
        # Idempotency: check if booking with same client_token already exists
        client_token_str = str(validated['client_token'])
        existing_payment = Payment.objects.filter(provider_ref=client_token_str).first()
        if existing_payment:
            return existing_payment.booking

        # Create booking with payment atomically using row-level locking to prevent race conditions
        with transaction.atomic():
            # Lock the room row to prevent concurrent bookings
            room = Room.objects.select_for_update().get(pk=validated['room_id'])
            
            # Double-check room availability within the transaction with locked room
            # This is needed because validation happens outside the transaction
            overlapping = Booking.objects.filter(
                room=room,
                status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                check_in__lt=validated['check_out'],
                check_out__gt=validated['check_in'],
            ).exists()
            
            if overlapping:
                raise serializers.ValidationError("Room is not available for the selected dates")
            
            # Get or create guest
            guest_data = validated['guest']
            guest, _ = Guest.objects.get_or_create(
                email=guest_data['email'],
                defaults=dict(
                    full_name=guest_data['full_name'],
                    phone=guest_data.get('phone', '')
                )
            )
            
            # Calculate total
            nights = (validated['check_out'] - validated['check_in']).days
            total_cents = room.price_cents * nights

            # Create booking
            booking = Booking.objects.create(
                room=room, 
                guest=guest,
                check_in=validated['check_in'], 
                check_out=validated['check_out'],
                total_cents=total_cents, 
                status=Booking.Status.PENDING
            )
            
            # Create associated payment
            Payment.objects.create(
                booking=booking, 
                amount_cents=total_cents,
                status=Payment.Status.PENDING,
                provider_ref=client_token_str
            )
            
        return booking

    def update(self, instance, validated_data):
        """Update booking instance - handle guest info and booking details"""
        
        with transaction.atomic():
            # Lock the current booking to prevent concurrent updates
            instance = Booking.objects.select_for_update().get(pk=instance.pk)
            
            # Handle guest information updates
            if 'guest' in validated_data:
                guest_data = validated_data.pop('guest')
                guest = instance.guest
                
                # Update guest information
                for attr, value in guest_data.items():
                    setattr(guest, attr, value)
                guest.save()
                
            # Handle room change
            if 'room_id' in validated_data:
                new_room_id = validated_data.pop('room_id')
                new_room = Room.objects.select_for_update().get(pk=new_room_id)
                
                # Check availability for new room if dates are changing or room is changing
                check_in = validated_data.get('check_in', instance.check_in)
                check_out = validated_data.get('check_out', instance.check_out)
                
                # Check for overlapping bookings (excluding current booking)
                overlapping = Booking.objects.filter(
                    room_id=new_room_id,
                    status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                    check_in__lt=check_out,
                    check_out__gt=check_in,
                ).exclude(pk=instance.pk).exists()
                
                if overlapping:
                    raise serializers.ValidationError("Room is not available for the selected dates")
                
                instance.room = new_room
                
                # Recalculate total if room changed
                nights = (check_out - check_in).days
                instance.total_cents = new_room.price_cents * nights

            # Handle date changes
            if 'check_in' in validated_data or 'check_out' in validated_data:
                check_in = validated_data.get('check_in', instance.check_in)
                check_out = validated_data.get('check_out', instance.check_out)
                
                # Validate dates
                if check_out <= check_in:
                    raise serializers.ValidationError("check_out must be after check_in")
                
                # Check availability for date changes (only if room didn't change)
                if 'room_id' not in validated_data:
                    overlapping = Booking.objects.filter(
                        room=instance.room,
                        status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                        check_in__lt=check_out,
                        check_out__gt=check_in,
                    ).exclude(pk=instance.pk).exists()
                    
                    if overlapping:
                        raise serializers.ValidationError("Room is not available for the selected dates")
                
                # Recalculate total for date changes
                nights = (check_out - check_in).days
                instance.total_cents = instance.room.price_cents * nights
                
                # Update payment amount if exists
                if hasattr(instance, 'payment'):
                    instance.payment.amount_cents = instance.total_cents
                    instance.payment.save()

            # Update other fields
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            
            instance.save()
            
        return instance
    

        