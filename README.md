# Hotel Reservation System

A comprehensive hotel reservation system built with Django REST Framework backend and Vue.js frontend, designed for both guest and staff interactions.

## Architecture Overview

### System Components

The Hotel Reservation System follows a three-tier architecture:

**Frontend Layer (Vue.js)**
- Guest Portal for room booking and management
- Staff Portal for administrative tasks
- Responsive web interface with TypeScript
- Real-time communication with backend via REST API

**Backend Layer (Django REST Framework)**
- RESTful API endpoints for all operations
- Business logic and data validation
- Room, booking, guest, and payment management
- CORS-enabled for frontend integration

**Database Layer (PostgreSQL)**
- Persistent data storage for all entities
- Relational data model with proper constraints
- Stores rooms, guests, bookings, and payment records
- Optimized for concurrent access and data integrity

The frontend communicates with the backend through HTTP requests, while the backend manages all database operations and business rules.

## Project Structure

```
hotel_reservation_project/
├── hotel_reservation_backend/          # Django REST API
│   ├── hotel_reservation/              # Main app
│   │   ├── models.py                   # Database models
│   │   ├── views.py                    # API endpoints
│   │   ├── serializers.py              # Data serialization
│   │   ├── urls.py                     # URL routing
│   │   └── management/commands/        # Custom commands
│   ├── hotel_reservation_backend/      # Project settings
│   ├── requirements.txt                # Python dependencies
│   ├── docker-compose.yml              # Database setup
│   └── Dockerfile                      # Backend containerization
│
├── hotel_reservation_frontend/         # Vue.js application
│   ├── src/
│   │   ├── components/                 # Reusable components
│   │   │   ├── BookingForm.vue
│   │   │   ├── StaffBookingForm.vue
│   │   │   ├── RoomForm.vue
│   │   │   └── Navigation.vue
│   │   ├── views/                      # Page components
│   │   │   ├── Home.vue
│   │   │   ├── Staff.vue
│   │   │   └── GuestBookings.vue
│   │   ├── services/                   # API communication
│   │   ├── stores/                     # State management
│   │   └── types/                      # TypeScript definitions
│   ├── package.json                    # Node dependencies
│   └── Dockerfile                      # Frontend containerization
│
└── run.sh                              # Development setup script
```

## Features

### Guest Portal
- **Room Search**: Filter available rooms by date and price
- **Booking Creation**: Book rooms with guest information
- **Payment Simulation**: Complete booking with simulated payment
- **Booking Management**: View and cancel bookings
- **My Bookings**: Dedicated page for guest bookings

### Staff Portal
- **Room Management**: Create, update, and view rooms
- **Booking Management**: Create and edit bookings on behalf of guests
- **Guest Information**: Manage guest details with free-text input
- **Dashboard**: Comprehensive view of all bookings and rooms

## Database Schema

### Core Models

#### Room
```python
- id: Primary key
- number: Unique room identifier
- room_type: Optional room category (Standard, Deluxe, Suite, etc.)
- price_cents: Price per night in cents
- capacity: Maximum guest capacity
- description: Room description
```

#### Guest
```python
- id: Primary key
- full_name: Guest full name
- email: Contact email
- phone: Phone number
```

#### Booking
```python
- id: Primary key
- room: Foreign key to Room
- guest: Foreign key to Guest
- check_in: Check-in date
- check_out: Check-out date
- total_cents: Total booking amount
- status: PENDING | CONFIRMED | CANCELLED
- created_at: Booking creation timestamp
```

#### Payment
```python
- id: Primary key
- booking: One-to-one with Booking
- amount_cents: Payment amount
- status: PENDING | PAID | FAILED | REFUNDED
- provider_ref: Payment provider reference
- created_at: Payment creation timestamp
```

## API Endpoints

### Rooms
- `GET /api/rooms/` - List available rooms with date/price filtering
- `POST /api/rooms/` - Create new room (staff only)
- `PUT /api/rooms/{id}/` - Update room (staff only)
- `DELETE /api/rooms/{id}/` - Delete room (staff only)

### Bookings
- `GET /api/bookings/` - List all bookings (staff only)
- `POST /api/bookings/` - Create new booking
- `GET /api/bookings/{id}/` - Get booking details
- `PATCH /api/bookings/{id}/` - Update booking status
- `GET /api/bookings/by_email/` - Get bookings by email
- `POST /api/bookings/{id}/confirm_payment/` - Process payment

## Technology Stack

### Backend
- **Framework**: Django 4.x with Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: Simulated (no actual auth required)
- **Validation**: Django model validation
- **CORS**: Enabled for frontend communication

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Routing**: Vue Router
- **State Management**: Pinia stores
- **HTTP Client**: Axios

### DevOps
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL in Docker
- **Development**: Hot reload for both frontend and backend

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- PostgreSQL (or use Docker setup)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hotel_reservation_project
   ```

2. **Run the setup script**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

### Manual Setup

#### Backend Setup
```bash
cd hotel_reservation_backend

# Start PostgreSQL with Docker
docker-compose up -d

# Install dependencies (no virtual environment as requested)
pip3 install -r requirements.txt

# Run migrations
python3 manage.py migrate

# Populate sample data
python3 manage.py populate_db

# Start development server
python3 manage.py runserver
```

#### Frontend Setup
```bash
cd hotel_reservation_frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Key Design Decisions

### 1. **No Authentication Required**
- Simplified development by using simulated authentication
- Guest identification through email-based lookups
- Staff access through dedicated routes

### 2. **Optional Room Types**
- Made room_type field optional for flexibility
- Frontend gracefully handles empty room types
- Allows hotels to manage rooms without rigid categorization

### 3. **Booking Status Simplification**
- Removed CHECK_IN/CHECK_OUT statuses as requested
- Focuses on core reservation states: PENDING, CONFIRMED, CANCELLED
- Simplifies workflow for both guests and staff

### 4. **Staff Workflow Optimization**
- Removed booking deletion to prevent data loss
- Enabled free-text guest information entry
- Streamlined booking management interface

### 5. **Guest Experience Enhancement**
- View Booking button routes to dedicated My Bookings page
- Integrated payment simulation
- Responsive design for mobile compatibility

## Future Enhancements

### Potential Improvements
1. **Real Authentication**: Implement JWT-based authentication
2. **Email Notifications**: Send booking confirmations and reminders
3. **Advanced Filtering**: Add amenity-based room filtering
4. **Reporting**: Staff analytics and occupancy reports
5. **Multi-language Support**: Internationalization
6. **Real Payment Integration**: Stripe, PayPal, or similar
7. **Calendar View**: Visual booking calendar for staff
8. **Room Availability Calendar**: Guest-facing availability calendar

### Scalability Considerations
1. **Caching**: Redis for session and query caching
2. **Load Balancing**: Multiple backend instances
3. **CDN**: Static asset delivery
4. **Database Optimization**: Indexing and query optimization
5. **Microservices**: Split payment and notification services

## Testing

### Backend Testing
```bash
cd hotel_reservation_backend
python3 manage.py test
```

### Frontend Testing
```bash
cd hotel_reservation_frontend
npm run test
```

## Deployment

The application is designed to be easily deployable using Docker:

```bash
# Build and run with Docker Compose
docker-compose up --build
```

This setup provides a production-ready environment with proper database persistence and networking.

## Support

For questions or issues, please refer to the assignment documentation or create an issue in the repository.
