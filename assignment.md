import pypandoc

# Markdown content for the project overview
markdown_content = """# Mini Hotel Reservation System

## Project Overview

**Deadline:** Submit before (17-08-2025)

Build a mini hotel reservation system with:

- **Backend API** (room, bookings).
- **Frontend dashboard** (basic search room, booking).
- **Database** (design your own).
- **Basic DevOps** (Docker, deployment).

Kindly utilize GitHub for project submission.

---

## Core Requirements

### 1. Backend (API)
- **Auth**: Not required (simulated).
- **Frameworks**: Any, but preferred Django. Other options: Node.js (Express), Python (FastAPI), Java (Spring), C# (ASP.NET Core).
- **Endpoints**:
  - `GET /rooms` – Search available rooms (filter by dates/price/amenities is bonus).
  - `POST /bookings` – Create a booking (guest id, guest details, room, dates, etc).
  - `GET /bookings/:id` – View booking details.
  - `PATCH /bookings/:id` – Cancel a booking.
- **Database**:
  - Use **SQL** (preferred PostgreSQL).
  - Normalized schema.

### 2. Frontend (Dashboard & Guest Frontend)
- **Frameworks**: React, Vue, Angular, or Svelte.
- **Features**:
  - **Guest View**:
    - Search rooms by date/price (date picker UI).
    - Book a room (form with validation).
    - View/cancel bookings.
    - Simulated payment flow.
  - **Staff View (bonus)**:
    - Add/edit rooms.
    - View all bookings (filter by date/status).
- **UI Libraries**: Tailwind CSS or plain CSS.

### 3. DevOps (Bonus)
- Dockerize backend + frontend.

### 4. Testing & Documentation
- **Backend**: Test booking conflicts (e.g., double-booking).
- **Frontend**: Test form validation, API error handling.
- **README**: Architecture diagram, trade-offs, setup guide.
- **Unit Testing**: Bonus.

### 5. Functional Requirements
- Guest can search for rooms.
- Guest can book a room.
- Guest can view bookings.
- Guest can cancel a booking.
- Guest can complete a simulated payment.
- Staff can view all rooms.
- Staff can view all bookings.

---

## Deliverables
- GitHub repository with backend + frontend source code.
- Docker setup (optional but bonus).
- Documentation (README, architecture diagram).
- Tests for backend and frontend.
"""

# Save the content as .md file
output_path = "/mnt/data/hotel_reservation_system.md"
with open(output_path, "w") as f:
    f.write(markdown_content)

output_path
