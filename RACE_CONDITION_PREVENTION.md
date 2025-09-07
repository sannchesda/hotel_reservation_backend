# Race Condition and Booking Conflict Prevention

This document explains the comprehensive measures implemented to prevent race conditions and booking conflicts in the hotel reservation system.

## Overview

The hotel reservation system has been hardened against race conditions and booking conflicts through multiple layers of protection:

1. **Database-Level Constraints**
2. **Row-Level Locking**
3. **Application-Level Validation**
4. **Idempotency Mechanisms**
5. **Comprehensive Testing**

## 1. Database-Level Constraints

### Indexes Added (Migration 0004)
```sql
-- Performance index for date range queries
CREATE INDEX idx_booking_room_dates ON hotel_reservation_booking 
(room_id, check_in, check_out) WHERE status IN ('CONFIRMED', 'PENDING');

-- Status filtering index
CREATE INDEX idx_booking_status ON hotel_reservation_booking (status);
```

### Benefits
- Faster overlap detection queries
- Improved performance for availability checks
- Database-enforced uniqueness at the lowest level

## 2. Row-Level Locking

### Implementation in `serializers.py`

#### Booking Creation
```python
with transaction.atomic():
    # Lock the room row to prevent concurrent bookings
    room = Room.objects.select_for_update().get(pk=validated['room_id'])
    
    # Check availability within the locked transaction
    overlapping = Booking.objects.filter(
        room=room,
        status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
        check_in__lt=validated['check_out'],
        check_out__gt=validated['check_in'],
    ).exists()
    
    if overlapping:
        raise serializers.ValidationError("Room is not available for the selected dates")
    
    # Create booking and payment atomically
    # ...
```

#### Booking Updates
```python
with transaction.atomic():
    # Lock the current booking to prevent concurrent updates
    instance = Booking.objects.select_for_update().get(pk=instance.pk)
    
    # Perform availability checks and updates within the locked transaction
    # ...
```

### Benefits
- Prevents multiple requests from booking the same room simultaneously
- Ensures atomic operations for booking creation and updates
- Eliminates race conditions between availability check and booking creation

## 3. Application-Level Validation

### Multi-Layer Validation in BookingSerializer

```python
def validate(self, data):
    # Date validation
    check_in = data.get('check_in')
    check_out = data.get('check_out')
    
    # For updates, get current instance dates if not provided
    if self.instance:
        check_in = check_in or self.instance.check_in
        check_out = check_out or self.instance.check_out
    
    if check_in and check_out and check_out <= check_in:
        raise serializers.ValidationError("check_out must be after check_in")
    
    # Overlap validation for creation
    if not self.instance and 'room_id' in data and check_in and check_out:
        # Check for idempotent requests first
        client_token_str = str(data['client_token'])
        existing_payment = Payment.objects.filter(provider_ref=client_token_str).first()
        
        if not existing_payment:
            # Check for overlapping bookings
            overlapping = Booking.objects.filter(
                room_id=data['room_id'],
                status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING],
                check_in__lt=check_out,
                check_out__gt=check_in,
            ).exists()
            
            if overlapping:
                raise serializers.ValidationError("Room is not available for the selected dates")
    
    # Overlap validation for updates
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
```

### Benefits
- Early validation before database operations
- Prevents invalid data from reaching the database
- Handles both creation and update scenarios
- Respects idempotency for duplicate requests

## 4. Idempotency Mechanisms

### Client Token System
Every booking creation requires a unique `client_token`. If the same token is used:

```python
# Check if booking with same client_token already exists
client_token_str = str(validated['client_token'])
existing_payment = Payment.objects.filter(provider_ref=client_token_str).first()
if existing_payment:
    return existing_payment.booking  # Return existing booking
```

### Benefits
- Prevents duplicate bookings from network retries
- Ensures safe retry behavior for clients
- Maintains system consistency under network failures

## 5. Comprehensive Testing

### Test Categories Implemented

#### Race Condition Tests (`RaceConditionTestCase`)
- **Concurrent Booking Attempts**: Tests multiple simultaneous booking requests for the same room
- **Room Availability Under Load**: Tests availability checking under concurrent load

#### Booking Conflict Tests (`BookingConflictTestCase`)
- **Overlapping Date Scenarios**: Tests all possible date overlap situations
- **Non-overlapping Bookings**: Validates that valid bookings are allowed
- **Cancelled Booking Handling**: Ensures cancelled bookings don't block new ones

#### Idempotency Tests (`IdempotencyTestCase`)
- **Duplicate Client Token Handling**: Tests that same client_token returns same booking
- **Different Token Behavior**: Validates that different tokens create separate bookings

#### Payment Integration Tests (`PaymentAndBookingStatusTestCase`)
- **Successful Payment Processing**: Tests payment confirmation workflow
- **Failed Payment Handling**: Tests failed payment scenarios

#### Booking Update Tests (`BookingUpdateTestCase`)
- **Room Change Validation**: Tests room changes with availability checking
- **Date Change Validation**: Tests date changes with conflict detection

### Example Race Condition Test
```python
def test_concurrent_booking_attempts_race_condition(self):
    """Test that concurrent booking attempts for the same room/dates don't create conflicts"""
    
    def create_booking(guest_email, client_token):
        # Booking creation logic
        pass
    
    # Create multiple concurrent booking attempts
    num_attempts = 5
    results = []
    
    with ThreadPoolExecutor(max_workers=num_attempts) as executor:
        futures = []
        for i in range(num_attempts):
            future = executor.submit(create_booking, f'test{i}@example.com', str(uuid.uuid4()))
            futures.append(future)
        
        for future in as_completed(futures):
            results.append(future.result())
    
    # Verify only one booking succeeded
    successful_bookings = [r for r in results if r['success']]
    self.assertEqual(len(successful_bookings), 1)
```

## 6. Database Migration Strategy

### Why Fresh Database for Tests?
Django creates a fresh test database for each test run because:

1. **Test Isolation**: Ensures tests don't interfere with each other
2. **Consistency**: Provides predictable starting conditions
3. **Migration Validation**: Tests that migrations work correctly
4. **Performance**: Fresh databases are typically faster
5. **Schema Validation**: Validates current model definitions

### Connection Pool Management
The connection pool issues during testing are managed by:
- Using `--parallel 1` for sequential test execution
- Using `--keepdb` to preserve test database between runs
- Proper transaction cleanup in test cases

## 7. Performance Considerations

### Optimizations Implemented
- Database indexes for faster overlap detection
- Row-level locking instead of table-level locking
- Early validation to avoid unnecessary database operations
- Efficient query patterns for availability checking

### Query Analysis
The overlap detection query:
```sql
SELECT EXISTS(
    SELECT 1 FROM hotel_reservation_booking 
    WHERE room_id = ? 
    AND status IN ('CONFIRMED', 'PENDING')
    AND check_in < ? 
    AND check_out > ?
)
```

Uses the `idx_booking_room_dates` index for optimal performance.

## 8. Deployment Considerations

### Production Recommendations
1. **Database Connection Pooling**: Use proper connection pooling (e.g., pgpool, connection pooler)
2. **Monitoring**: Monitor for deadlocks and long-running transactions
3. **Load Testing**: Regularly test under concurrent load
4. **Database Maintenance**: Regular index maintenance and query optimization

### Scaling Considerations
- Row-level locking scales better than table-level locking
- Database indexes improve performance as data grows
- Consider read replicas for availability queries if needed

## 9. Error Handling

### Common Error Scenarios
- **ValidationError**: Raised for booking conflicts
- **IntegrityError**: Database-level constraint violations (backup safety)
- **Transaction Rollback**: Automatic rollback on any error within transaction

### Client Response Examples
```json
// Successful booking
{
    "id": 123,
    "room": {...},
    "guest": {...},
    "status": "PENDING"
}

// Booking conflict
{
    "non_field_errors": ["Room is not available for the selected dates"]
}

// Idempotent request
{
    "id": 123,  // Same booking ID returned
    "room": {...},
    "guest": {...},
    "status": "PENDING"
}
```

## Conclusion

The implemented solution provides multiple layers of protection against race conditions and booking conflicts:

1. **Database indexes** for performance
2. **Row-level locking** for transaction safety
3. **Application validation** for early error detection
4. **Idempotency** for safe retries
5. **Comprehensive testing** for confidence

This multi-layered approach ensures data consistency, prevents double-bookings, and maintains system reliability under concurrent load.
