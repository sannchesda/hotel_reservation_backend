# Hotel Reservation System

A simple project of Hotel Reservation System using Django, VueJs, and PostgreSQL

## Demo Project

https://hotelreservationfrontend-production.up.railway.app/

## Architecture Overview

### System Components

The Hotel Reservation System follows a three-tier architecture:

**Frontend Layer (Vue.js)**
- Guest Portal for room booking and management
- Staff Portal for administrative tasks
- Real-time communication with backend via REST API

**Backend Layer (Django REST Framework)**
- Business logic and data validation
- Room, booking, guest, and payment management
- CORS-enabled for frontend integration
- Prevent race condition and booking conflict on App and Database level

**Database Layer (PostgreSQL)**
- Persistent data storage for all entities
- Relational data model with proper constraints
- Stores rooms, guests, bookings, and payment records

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
│   ├── docker-compose.yml              # Local Database setup
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
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL (or use Docker setup)

### Manual Setup

#### Backend Setup
```bash
cd hotel_reservation_backend

# Set up Local DB
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
