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

def welcome(request):
    return JsonResponse({"message": "Welcome to the Hotel Reservation System"})

def health_check(request):
    return JsonResponse({"status": "ok"})

def available_rooms_qs(check_in, check_out, max_price=None):
    overlap = Exists(
        Booking.objects.filter(
            room=OuterRef('pk'),
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
            check_in__lt=check_out,
            check_out__gt=check_in,
        )
    )
    qs = Room.objects.annotate(has_overlap=overlap).filter(has_overlap=False)
    if max_price is not None:
        qs = qs.filter(price_cents__lte=max_price)
    return qs

class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer

    def list(self, request):
        """Search available rooms with filters"""
        check_in_str = request.query_params.get('check_in')
        check_out_str = request.query_params.get('check_out')
        max_price = request.query_params.get('max_price')
        
        if check_in_str and check_out_str:
            try:
                check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
                check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
                
                # Get available rooms for the date range
                rooms = available_rooms_qs(check_in, check_out, 
                                         int(max_price) * 100 if max_price else None)
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

    @action(detail=False, methods=['get'])
    def by_email(self, request):
        """Get bookings by guest email"""
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Email parameter is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        bookings = Booking.objects.filter(guest__email=email).order_by('-created_at')
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get current user's bookings (simulated authentication)"""
        # In a real app, this would use request.user
        # For simulation, we get email from query params or session
        email = request.query_params.get('user_email')
        if not email:
            return Response({'error': 'User not authenticated'}, 
                            status=status.HTTP_401_UNAUTHORIZED)
        
        bookings = Booking.objects.filter(guest__email=email).order_by('-created_at')
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    def update(self, request, pk=None, **kwargs):
        """Update a booking - full access for staff, limited access for guests"""
        try:
            booking = self.get_object()
            user_type = request.data.get('user_type', 'guest')  # Default to guest if not specified
            
            # Handle cancellation (allowed for both staff and guests)
            if 'status' in request.data and request.data['status'] == 'CANCELLED':
                booking.status = Booking.Status.CANCELLED
                booking.save()
                
                # Update payment status to refunded if it was paid
                if hasattr(booking, 'payment') and booking.payment.status == Payment.Status.PAID:
                    booking.payment.status = Payment.Status.REFUNDED
                    booking.payment.save()
                
                serializer = self.get_serializer(booking)
                return Response(serializer.data)
            
        
            # Staff can edit any booking information
            if user_type == 'staff':
                # Use serializer to handle full updates including guest info
                serializer = self.get_serializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Guests can only cancel bookings (already handled above)
            else:
                return Response({'error': 'Only cancellation is allowed for guests'}, 
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
                    # Update booking status to CONFIRMED when payment is successful
                    booking.status = Booking.Status.CONFIRMED
                    booking.save()
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