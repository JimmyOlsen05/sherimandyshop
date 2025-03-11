from django.core.management.base import BaseCommand
from orders.models import DeliveryLocation

class Command(BaseCommand):
    help = 'Set up initial delivery locations'

    def handle(self, *args, **kwargs):
        # Create Tarkwa locations (free delivery)
        tarkwa_locations = [
            'Tarkwa Main',
            'UMaT Campus',
            'Aboso',
            'Tarkwa Banso',
            'New Atuabo',
        ]
        
        for name in tarkwa_locations:
            DeliveryLocation.objects.get_or_create(
                name=name,
                defaults={
                    'is_tarkwa': True,
                    'base_fee': 0,
                    'distance_km': 0
                }
            )
            self.stdout.write(f'Created Tarkwa location: {name}')
        
        # Create other locations with distance-based fees
        other_locations = [
            ('Takoradi', 85, 30),  # 85km from Tarkwa, GH₵30 base fee
            ('Kumasi', 320, 50),   # 320km from Tarkwa, GH₵50 base fee
            ('Accra', 317, 50),    # 317km from Tarkwa, GH₵50 base fee
            ('Cape Coast', 230, 40), # 230km from Tarkwa, GH₵40 base fee
            ('Obuasi', 250, 45),    # 250km from Tarkwa, GH₵45 base fee
            ('Prestea', 45, 20),    # 45km from Tarkwa, GH₵20 base fee
            ('Bogoso', 35, 15),     # 35km from Tarkwa, GH₵15 base fee
        ]
        
        for name, distance, base_fee in other_locations:
            DeliveryLocation.objects.get_or_create(
                name=name,
                defaults={
                    'is_tarkwa': False,
                    'base_fee': base_fee,
                    'distance_km': distance
                }
            )
            self.stdout.write(f'Created location: {name} ({distance}km)')
