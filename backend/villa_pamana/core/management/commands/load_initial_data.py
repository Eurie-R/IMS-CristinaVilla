from django.core.management.base import BaseCommand
from core.models import InventoryCategory, FinancialCategory, Room

class Command(BaseCommand):
    help = 'Load initial data'

    def handle(self, *args, **kwargs):
        # Create inventory categories
        categories = ['Kitchen', 'Housekeeping', 'Maintenance', 'Office']
        for cat in categories:
            InventoryCategory.objects.get_or_create(name=cat)
        
        # Create financial categories
        FinancialCategory.objects.get_or_create(name='Room Booking', type='income')
        FinancialCategory.objects.get_or_create(name='Services', type='income')
        FinancialCategory.objects.get_or_create(name='Supplies', type='expense')
        FinancialCategory.objects.get_or_create(name='Utilities', type='expense')
        FinancialCategory.objects.get_or_create(name='Salaries', type='expense')
        
        # Create sample rooms
        rooms = [
            {'room_number': '101', 'room_type': 'single', 'capacity': 1, 'rate_per_night': 1500},
            {'room_number': '102', 'room_type': 'double', 'capacity': 2, 'rate_per_night': 2500},
            {'room_number': '103', 'room_type': 'suite', 'capacity': 4, 'rate_per_night': 4500},
        ]
        for room in rooms:
            Room.objects.get_or_create(**room)
        
        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully'))