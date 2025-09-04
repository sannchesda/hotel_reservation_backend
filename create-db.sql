-- rooms & amenities
CREATE TABLE amenities (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE rooms (
    id SERIAL PRIMARY KEY,
    number TEXT UNIQUE NOT NULL,
    room_type TEXT NOT NULL,
    -- "single", "double", "suite"
    price_cents INT NOT NULL CHECK (price_cents >= 0),
    capacity INT NOT NULL CHECK (capacity > 0),
    description TEXT DEFAULT ''
);

CREATE TABLE room_amenities (
    room_id INT REFERENCES rooms(id) ON DELETE CASCADE,
    amenity_id INT REFERENCES amenities(id) ON DELETE CASCADE,
    PRIMARY KEY (room_id, amenity_id)
);

-- guests
CREATE TABLE guests (
    id SERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT
);

-- bookings
CREATE TYPE booking_status AS ENUM ('CONFIRMED', 'CANCELLED');

CREATE TABLE bookings (
    id SERIAL PRIMARY KEY,
    room_id INT NOT NULL REFERENCES rooms(id),
    guest_id INT NOT NULL REFERENCES guests(id),
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    -- exclusive
    total_cents INT NOT NULL CHECK (total_cents >= 0),
    status booking_status NOT NULL DEFAULT 'CONFIRMED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- prevent overlapping bookings for same room when status is CONFIRMED
CREATE UNIQUE INDEX uniq_room_date_no_overlap ON bookings (room_id, daterange(check_in, check_out, '[]'))
WHERE
    status = 'CONFIRMED' USING gist;

-- payments (simulated)
CREATE TYPE payment_status AS ENUM ('PENDING', 'PAID', 'FAILED', 'REFUNDED');

CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    booking_id INT UNIQUE REFERENCES bookings(id) ON DELETE CASCADE,
    amount_cents INT NOT NULL,
    status payment_status NOT NULL DEFAULT 'PENDING',
    provider_ref TEXT,
    -- fake token/id
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);