from django.test import TestCase, TransactionTestCase
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import Room, Booking, Guest, Payment
from .serializers import BookingSerializer


class RaceConditionTestCase(TransactionTestCase):
    """Test race conditions in booking creation"""
    
    def setUp(self):
        self.room = Room.objects.create(
            number="101",
            room_type="Standard",
            price_cents=10000,
            capacity=2,
            description="Test room"
        )
        self.check_in = date.today() + timedelta(days=1)
        self.check_out = date.today() + timedelta(days=3)
    
    def test_concurrent_booking_attempts_race_condition(self):
        """Test that concurrent booking attempts for the same room/dates don't create conflicts"""
        
        def create_booking(guest_email, client_token):
            """Helper function to create a booking"""
            try:
                serializer = BookingSerializer(data={
                    'room_id': self.room.id,
                    'guest': {
                        'full_name': f'Test Guest {guest_email}',
                        'email': guest_email,
                        'phone': '123-456-7890'
                    },
                    'check_in': self.check_in,
                    'check_out': self.check_out,
                    'client_token': client_token
                })
                
                if serializer.is_valid():
                    booking = serializer.save()
                    return {'success': True, 'booking_id': booking.id}
                else:
                    return {'success': False, 'errors': serializer.errors}
                    
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Create multiple concurrent booking attempts
        num_attempts = 5
        results = []
        
        with ThreadPoolExecutor(max_workers=num_attempts) as executor:
            futures = []
            for i in range(num_attempts):
                future = executor.submit(
                    create_booking,
                    f'test{i}@example.com',
                    str(uuid.uuid4())
                )
                futures.append(future)
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Count successful bookings
        successful_bookings = [r for r in results if r['success']]
        failed_bookings = [r for r in results if not r['success']]
        
        # Only one booking should succeed
        self.assertEqual(len(successful_bookings), 1, 
                        f"Expected exactly 1 successful booking, got {len(successful_bookings)}")
        self.assertEqual(len(failed_bookings), num_attempts - 1,
                        f"Expected {num_attempts - 1} failed bookings, got {len(failed_bookings)}")
        
        # Verify only one booking exists in database
        booking_count = Booking.objects.filter(
            room=self.room,
            check_in=self.check_in,
            check_out=self.check_out
        ).count()
        self.assertEqual(booking_count, 1, "Expected exactly 1 booking in database")
    
    def test_concurrent_room_availability_check(self):
        """Test that room availability checks work correctly under concurrent load"""
        
        # Create multiple rooms
        rooms = []
        for i in range(3):
            room = Room.objects.create(
                number=f"10{i+2}",
                room_type="Standard",
                price_cents=10000,
                capacity=2
            )
            rooms.append(room)
        
        def book_any_available_room(guest_num):
            """Try to book any available room"""
            try:
                # Simulate checking availability first
                from .views import available_rooms_qs
                available = available_rooms_qs(self.check_in, self.check_out)
                
                if available.exists():
                    room = available.first()
                    
                    serializer = BookingSerializer(data={
                        'room_id': room.id,
                        'guest': {
                            'full_name': f'Guest {guest_num}',
                            'email': f'guest{guest_num}@example.com',
                        },
                        'check_in': self.check_in,
                        'check_out': self.check_out,
                        'client_token': str(uuid.uuid4())
                    })
                    
                    if serializer.is_valid():
                        booking = serializer.save()
                        return {'success': True, 'room_id': room.id}
                    else:
                        return {'success': False, 'errors': serializer.errors}
                else:
                    return {'success': False, 'error': 'No rooms available'}
                    
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        # Try to book rooms concurrently
        num_guests = 10
        results = []
        
        with ThreadPoolExecutor(max_workers=num_guests) as executor:
            futures = [executor.submit(book_any_available_room, i) for i in range(num_guests)]
            for future in as_completed(futures):
                results.append(future.result())
        
        successful_bookings = [r for r in results if r['success']]
        
        # Should not exceed the number of available rooms
        self.assertLessEqual(len(successful_bookings), len(rooms) + 1,  # +1 for the original room
                           "More bookings succeeded than rooms available")


class BookingConflictTestCase(APITestCase):
    """Test booking conflict scenarios"""
    
    def setUp(self):
        self.room = Room.objects.create(
            number="201",
            room_type="Deluxe",
            price_cents=15000,
            capacity=2
        )
        
        self.guest = Guest.objects.create(
            full_name="Test Guest",
            email="test@example.com"
        )
    
    def test_overlapping_date_booking_conflict(self):
        """Test that overlapping date bookings are rejected"""
        
        # Create first booking
        booking1 = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=5),
            total_cents=60000,
            status=Booking.Status.CONFIRMED
        )
        
        # Try to create overlapping booking
        overlap_scenarios = [
            # Scenario 1: New booking starts before existing and overlaps
            {
                'check_in': date.today(),
                'check_out': date.today() + timedelta(days=3),
                'description': 'starts before and overlaps'
            },
            # Scenario 2: New booking starts during existing booking
            {
                'check_in': date.today() + timedelta(days=2),
                'check_out': date.today() + timedelta(days=6),
                'description': 'starts during existing booking'
            },
            # Scenario 3: New booking is completely within existing booking
            {
                'check_in': date.today() + timedelta(days=2),
                'check_out': date.today() + timedelta(days=4),
                'description': 'completely within existing booking'
            },
            # Scenario 4: New booking completely encompasses existing booking
            {
                'check_in': date.today(),
                'check_out': date.today() + timedelta(days=6),
                'description': 'completely encompasses existing booking'
            }
        ]
        
        for scenario in overlap_scenarios:
            with self.subTest(scenario=scenario['description']):
                serializer = BookingSerializer(data={
                    'room_id': self.room.id,
                    'guest': {
                        'full_name': 'Another Guest',
                        'email': 'another@example.com',
                    },
                    'check_in': scenario['check_in'],
                    'check_out': scenario['check_out'],
                    'client_token': str(uuid.uuid4())
                })
                
                self.assertFalse(serializer.is_valid())
                self.assertIn('Room is not available', str(serializer.errors))
    
    def test_non_overlapping_bookings_allowed(self):
        """Test that non-overlapping bookings are allowed"""
        
        # Create first booking
        booking1 = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=10),
            total_cents=75000,
            status=Booking.Status.CONFIRMED
        )
        
        valid_scenarios = [
            # Before existing booking
            {
                'check_in': date.today() + timedelta(days=1),
                'check_out': date.today() + timedelta(days=5),  # Check-out same as check-in of existing
                'description': 'before existing booking'
            },
            # After existing booking
            {
                'check_in': date.today() + timedelta(days=10),  # Check-in same as check-out of existing
                'check_out': date.today() + timedelta(days=15),
                'description': 'after existing booking'
            }
        ]
        
        for scenario in valid_scenarios:
            with self.subTest(scenario=scenario['description']):
                serializer = BookingSerializer(data={
                    'room_id': self.room.id,
                    'guest': {
                        'full_name': 'Valid Guest',
                        'email': f'valid_{uuid.uuid4()}@example.com',
                    },
                    'check_in': scenario['check_in'],
                    'check_out': scenario['check_out'],
                    'client_token': str(uuid.uuid4())
                })
                
                self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
                booking = serializer.save()
                self.assertIsInstance(booking, Booking)
    
    def test_cancelled_booking_allows_overlap(self):
        """Test that cancelled bookings don't block new bookings"""
        
        # Create cancelled booking
        cancelled_booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=5),
            total_cents=60000,
            status=Booking.Status.CANCELLED
        )
        
        # Try to create overlapping booking - should succeed
        serializer = BookingSerializer(data={
            'room_id': self.room.id,
            'guest': {
                'full_name': 'New Guest',
                'email': 'new@example.com',
            },
            'check_in': date.today() + timedelta(days=2),
            'check_out': date.today() + timedelta(days=4),
            'client_token': str(uuid.uuid4())
        })
        
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")
        booking = serializer.save()
        self.assertEqual(booking.status, Booking.Status.PENDING)


class IdempotencyTestCase(APITestCase):
    """Test client token idempotency mechanism"""
    
    def setUp(self):
        self.room = Room.objects.create(
            number="301",
            room_type="Suite",
            price_cents=25000,
            capacity=4
        )
        
        self.booking_data = {
            'room_id': self.room.id,
            'guest': {
                'full_name': 'Idempotency Test Guest',
                'email': 'idempotency@example.com',
            },
            'check_in': date.today() + timedelta(days=1),
            'check_out': date.today() + timedelta(days=3),
        }
    
    def test_duplicate_client_token_returns_same_booking(self):
        """Test that using the same client token returns the existing booking"""
        
        client_token = str(uuid.uuid4())
        
        # Create first booking
        serializer1 = BookingSerializer(data={
            **self.booking_data,
            'client_token': client_token
        })
        self.assertTrue(serializer1.is_valid())
        booking1 = serializer1.save()
        
        # Try to create same booking with same client token
        serializer2 = BookingSerializer(data={
            **self.booking_data,
            'client_token': client_token
        })
        self.assertTrue(serializer2.is_valid())
        booking2 = serializer2.save()
        
        # Should return the same booking
        self.assertEqual(booking1.id, booking2.id)
        
        # Should only have one booking in database
        booking_count = Booking.objects.filter(room=self.room).count()
        self.assertEqual(booking_count, 1)
    
    def test_different_client_tokens_create_separate_bookings(self):
        """Test that different client tokens create separate bookings for different dates"""
        
        # Create first booking
        serializer1 = BookingSerializer(data={
            **self.booking_data,
            'client_token': str(uuid.uuid4())
        })
        self.assertTrue(serializer1.is_valid())
        booking1 = serializer1.save()
        
        # Create second booking with different dates and client token
        different_data = {
            **self.booking_data,
            'check_in': date.today() + timedelta(days=5),
            'check_out': date.today() + timedelta(days=7),
            'client_token': str(uuid.uuid4())
        }
        
        serializer2 = BookingSerializer(data=different_data)
        self.assertTrue(serializer2.is_valid())
        booking2 = serializer2.save()
        
        # Should create different bookings
        self.assertNotEqual(booking1.id, booking2.id)
        
        # Should have two bookings in database
        booking_count = Booking.objects.filter(room=self.room).count()
        self.assertEqual(booking_count, 2)


class PaymentAndBookingStatusTestCase(APITestCase):
    """Test payment processing and booking status changes"""
    
    def setUp(self):
        self.room = Room.objects.create(
            number="401",
            room_type="Presidential",
            price_cents=50000,
            capacity=6
        )
        
        self.guest = Guest.objects.create(
            full_name="Payment Test Guest",
            email="payment@example.com"
        )
        
        self.booking = Booking.objects.create(
            room=self.room,
            guest=self.guest,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            total_cents=100000,
            status=Booking.Status.PENDING
        )
        
        self.payment = Payment.objects.create(
            booking=self.booking,
            amount_cents=100000,
            status=Payment.Status.PENDING,
            provider_ref=str(uuid.uuid4())
        )
    
    def test_successful_payment_confirms_booking(self):
        """Test that successful payment changes booking status to confirmed"""
        
        # Simulate successful payment
        url = f'/api/bookings/{self.booking.id}/confirm_payment/'
        response = self.client.post(url, {
            'success': True,
            'provider_ref': 'payment_12345'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.booking.refresh_from_db()
        self.payment.refresh_from_db()
        
        self.assertEqual(self.booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(self.payment.status, Payment.Status.PAID)
    
    def test_failed_payment_keeps_booking_pending(self):
        """Test that failed payment doesn't change booking status"""
        
        # Simulate failed payment
        url = f'/api/bookings/{self.booking.id}/confirm_payment/'
        response = self.client.post(url, {
            'success': False
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        self.booking.refresh_from_db()
        self.payment.refresh_from_db()
        
        self.assertEqual(self.booking.status, Booking.Status.PENDING)
        self.assertEqual(self.payment.status, Payment.Status.FAILED)


class BookingUpdateTestCase(APITestCase):
    """Test booking update scenarios"""
    
    def setUp(self):
        # Create multiple rooms
        self.room1 = Room.objects.create(number="501", price_cents=10000, capacity=2)
        self.room2 = Room.objects.create(number="502", price_cents=15000, capacity=2)
        
        self.guest = Guest.objects.create(
            full_name="Update Test Guest",
            email="update@example.com"
        )
        
        self.booking = Booking.objects.create(
            room=self.room1,
            guest=self.guest,
            check_in=date.today() + timedelta(days=1),
            check_out=date.today() + timedelta(days=3),
            total_cents=20000,
            status=Booking.Status.PENDING
        )
    
    def test_room_change_with_availability_check(self):
        """Test changing room in booking with proper availability checking"""
        
        # Update booking to use different room
        serializer = BookingSerializer(self.booking, data={
            'room_id': self.room2.id,
            'guest': {
                'full_name': self.guest.full_name,
                'email': self.guest.email
            }
        }, partial=True)
        
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")
        updated_booking = serializer.save()
        
        self.assertEqual(updated_booking.room.id, self.room2.id)
        # Total should be recalculated based on new room price
        self.assertEqual(updated_booking.total_cents, 30000)  # 2 nights * 15000
    
    def test_date_change_with_conflict_check(self):
        """Test changing dates with proper conflict checking"""
        
        # Create conflicting booking first
        conflicting_booking = Booking.objects.create(
            room=self.room1,
            guest=Guest.objects.create(full_name="Conflict Guest", email="conflict@example.com"),
            check_in=date.today() + timedelta(days=5),
            check_out=date.today() + timedelta(days=8),
            total_cents=30000,
            status=Booking.Status.CONFIRMED
        )
        
        # Try to update booking to overlap with conflicting booking
        serializer = BookingSerializer(self.booking, data={
            'check_in': date.today() + timedelta(days=4),
            'check_out': date.today() + timedelta(days=6),
            'guest': {
                'full_name': self.guest.full_name,
                'email': self.guest.email
            }
        }, partial=True)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('Room is not available', str(serializer.errors))
