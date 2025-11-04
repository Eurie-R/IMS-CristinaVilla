from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    InventoryCategory, InventoryItem, Task, Room, Booking,
    FinancialCategory, Transaction, CalendarEvent
)

User = get_user_model()

# User Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']
        read_only_fields = ['id']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role', 'phone']
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

# Inventory Serializers
class InventoryCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryCategory
        fields = '__all__'

class InventoryItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    needs_restock = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InventoryItem
        fields = '__all__'

# Task Serializers
class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'

# Room Serializers
class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'

# Booking Serializers
class BookingSerializer(serializers.ModelSerializer):
    room_number = serializers.CharField(source='room.room_number', read_only=True)
    room_type = serializers.CharField(source='room.room_type', read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'

class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'
    
    def validate(self, data):
        # Check for overlapping bookings
        room = data.get('room')
        check_in = data.get('check_in_date')
        check_out = data.get('check_out_date')
        
        if check_in >= check_out:
            raise serializers.ValidationError("Check-out date must be after check-in date")
        
        overlapping = Booking.objects.filter(
            room=room,
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )
        
        if self.instance:
            overlapping = overlapping.exclude(pk=self.instance.pk)
        
        if overlapping.exists():
            raise serializers.ValidationError("Room is already booked for these dates")
        
        return data

# Financial Serializers
class FinancialCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialCategory
        fields = '__all__'

class TransactionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    booking_guest = serializers.CharField(source='booking.guest_name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'

# Calendar Serializers
class CalendarEventSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    booking_guest = serializers.CharField(source='related_booking.guest_name', read_only=True)
    
    class Meta:
        model = CalendarEvent
        fields = '__all__'

# Dashboard Serializers
class DashboardSerializer(serializers.Serializer):
    daily_tasks = TaskSerializer(many=True, read_only=True)
    restock_alerts = InventoryItemSerializer(many=True, read_only=True)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    monthly_expenses = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    monthly_profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    todays_checkins = BookingSerializer(many=True, read_only=True)
    todays_checkouts = BookingSerializer(many=True, read_only=True)
    available_rooms = serializers.IntegerField(read_only=True)
    occupied_rooms = serializers.IntegerField(read_only=True)