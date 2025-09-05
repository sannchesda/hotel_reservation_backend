from django.core.management.base import BaseCommand
from hotel_reservation.models import Room, Amenity


class Command(BaseCommand):
    help = 'Populate database with sample hotel data'

    def handle(self, *args, **options):
        # Create amenities
        amenities_data = [
            'WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Room Service',
            'Balcony', 'Ocean View', 'City View', 'Jacuzzi', 'Kitchenette'
        ]
        
        amenities = {}
        for amenity_name in amenities_data:
            amenity, created = Amenity.objects.get_or_create(name=amenity_name)
            amenities[amenity_name] = amenity
            if created:
                self.stdout.write(f'Created amenity: {amenity_name}')

        # Create rooms
        rooms_data = [
            {
                'number': '101',
                'room_type': 'Standard Room',
                'price_cents': 8000,  # $80
                'capacity': 2,
                'description': 'Comfortable standard room with city view',
                'amenities': ['WiFi', 'Air Conditioning', 'TV']
            },
            {
                'number': '102',
                'room_type': 'Standard Room',
                'price_cents': 8500,  # $85
                'capacity': 2,
                'description': 'Standard room with balcony',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Balcony']
            },
            {
                'number': '201',
                'room_type': 'Deluxe Room',
                'price_cents': 12000,  # $120
                'capacity': 3,
                'description': 'Spacious deluxe room with ocean view',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Ocean View']
            },
            {
                'number': '202',
                'room_type': 'Deluxe Room',
                'price_cents': 11500,  # $115
                'capacity': 3,
                'description': 'Deluxe room with city view and jacuzzi',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'City View', 'Jacuzzi']
            },
            {
                'number': '301',
                'room_type': 'Family Suite',
                'price_cents': 18000,  # $180
                'capacity': 4,
                'description': 'Large family suite with kitchenette',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Room Service', 'Kitchenette']
            },
            {
                'number': '302',
                'room_type': 'Family Suite',
                'price_cents': 20000,  # $200
                'capacity': 4,
                'description': 'Premium family suite with ocean view',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Room Service', 'Ocean View', 'Balcony']
            },
            {
                'number': '401',
                'room_type': 'Presidential Suite',
                'price_cents': 35000,  # $350
                'capacity': 6,
                'description': 'Luxury presidential suite with all amenities',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Room Service', 'Ocean View', 'Balcony', 'Jacuzzi', 'Kitchenette']
            },
            {
                'number': '501',
                'room_type': 'Penthouse',
                'price_cents': 50000,  # $500
                'capacity': 8,
                'description': 'Top floor penthouse with panoramic views',
                'amenities': ['WiFi', 'Air Conditioning', 'TV', 'Mini Bar', 'Room Service', 'Ocean View', 'City View', 'Balcony', 'Jacuzzi', 'Kitchenette']
            }
        ]

        for room_data in rooms_data:
            room_amenities = room_data.pop('amenities')
            room, created = Room.objects.get_or_create(
                number=room_data['number'],
                defaults=room_data
            )
            
            if created:
                # Add amenities to the room
                for amenity_name in room_amenities:
                    if amenity_name in amenities:
                        room.amenities.add(amenities[amenity_name])
                
                self.stdout.write(f'Created room: {room.number} - {room.room_type}')
            else:
                self.stdout.write(f'Room {room.number} already exists')

        self.stdout.write(
            self.style.SUCCESS('Successfully populated database with sample data')
        )
