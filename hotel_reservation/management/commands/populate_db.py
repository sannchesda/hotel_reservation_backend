from django.core.management.base import BaseCommand
from hotel_reservation.models import Room


class Command(BaseCommand):
    help = 'Populate database with sample hotel data'

    def handle(self, *args, **options):
        # Create rooms
        rooms_data = [
            {
                'number': '101',
                'room_type': 'Standard Room',
                'price_cents': 8000,  # $80
                'capacity': 2,
                'description': 'Comfortable standard room with city view'
            },
            {
                'number': '102',
                'room_type': 'Standard Room',
                'price_cents': 8500,  # $85
                'capacity': 2,
                'description': 'Standard room with balcony'
            },
            {
                'number': '201',
                'room_type': 'Deluxe Room',
                'price_cents': 12000,  # $120
                'capacity': 3,
                'description': 'Spacious deluxe room with ocean view'
            },
            {
                'number': '202',
                'room_type': 'Deluxe Room',
                'price_cents': 13000,  # $130
                'capacity': 3,
                'description': 'Deluxe room with city view and mini bar'
            },
            {
                'number': '301',
                'room_type': 'Family Suite',
                'price_cents': 18000,  # $180
                'capacity': 4,
                'description': 'Large family suite with kitchenette'
            },
            {
                'number': '302',
                'room_type': 'Family Suite',
                'price_cents': 20000,  # $200
                'capacity': 4,
                'description': 'Premium family suite with ocean view'
            },
            {
                'number': '401',
                'room_type': 'Presidential Suite',
                'price_cents': 35000,  # $350
                'capacity': 6,
                'description': 'Luxury presidential suite with all amenities'
            },
            {
                'number': '501',
                'room_type': 'Penthouse',
                'price_cents': 50000,  # $500
                'capacity': 8,
                'description': 'Top floor penthouse with panoramic views'
            }
        ]

        for room_data in rooms_data:
            room, created = Room.objects.get_or_create(
                number=room_data['number'],
                defaults=room_data
            )
            
            if created:
                self.stdout.write(f'Created room: {room.number} - {room.room_type}')
            else:
                self.stdout.write(f'Room {room.number} already exists')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data')
        )
