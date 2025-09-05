from django.shortcuts import render
from django.db.models import Exists, OuterRef, Q
from .models import Room, Booking, Payment
from django.http import JsonResponse
from .serializers import RoomSerializer, BookingSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import datetime, date
import uuid

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

    def list(self, request):
        """Search available rooms with filters"""
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        max_price = request.query_params.get('max_price')
        amenities = request.query_params.get('amenities')
        
        if check_in_str and check_out_str:
            try:
                check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
                
                # Get available rooms for the date range
                rooms = available_rooms_qs(check_in, check_out, 
                                         int(max_price) * 100 if max_price else None,
                                         amenities.split(',') if amenities else None)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return all rooms if no dates specified
            rooms = Room.objects.all()
            
        serializer = self.get_serializer(rooms, many=True)
        return Response(serializer.data)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def update(self, request, pk=None, **kwargs):
        """Cancel a booking"""
        try:
            booking = self.get_object()
            if 'status' in request.data and request.data['status'] == 'CANCELLED':
                booking.status = Booking.Status.CANCELLED
                booking.save()
                
                # Update payment status to refunded if it was paid
                if hasattr(booking, 'payment') and booking.payment.status == Payment.Status.PAID:
                    booking.payment.status = Payment.Status.REFUNDED
                    booking.payment.save()
                
                serializer = self.get_serializer(booking)
                return Response(serializer.data)
            else:
                return Response({'error': 'Only cancellation is allowed'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, 
                          status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, pk=None, **kwargs):
        """Handle partial updates (PATCH requests)"""
        return self.update(request, pk, **kwargs)

    @action(detail=True, methods=['post'])
    def confirm_payment(self, request, pk=None):
        """Simulate payment confirmation"""
        try:
            booking = self.get_object()
            if hasattr(booking, 'payment'):
                payment = booking.payment
                # Simulate payment processing
                success = request.data.get('success', True)
                
                if success:
                    payment.status = Payment.Status.PAID
                    payment.provider_ref = request.data.get('provider_ref', str(uuid.uuid4()))
                else:
                    payment.status = Payment.Status.FAILED
                
                payment.save()
                
                return Response({
                    'payment_status': payment.status,
                    'booking_id': booking.id,
                    'amount': payment.amount_cents / 100.0
                })
            else:
                return Response({'error': 'No payment found for this booking'}, 
                              status=status.HTTP_404_NOT_FOUND)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, 
                          status=status.HTTP_404_NOT_FOUND)