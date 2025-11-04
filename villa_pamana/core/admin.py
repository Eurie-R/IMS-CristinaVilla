from django.contrib import admin
from .models import InventoryItem, TodoTask, Booking, FinancialTransaction

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'quantity', 'unit', 'minimum_stock', 'last_updated', 'needs_restock']
    list_filter = ['category',]
    search_fields = ['name',]

@admin.register(TodoTask)
class TodoTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'is_completed', 'due_date', 'created_at']
    list_filter = ['priority', 'is_completed']
    search_fields = ['title', 'description']
    ordering = ['-priority', 'due_date']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['guest_name', 'contact_number', 'room_number', 
                    'number_of_guests', 'check_in', 'check_out', 
                    'payment_amount', 'payment_status','created_at']
    list_filter = ['room_number', 'check_in', 'check_out']
    search_fields = ['guest_name', 'contact_number']

@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'category', 'amount', 'description', 'date','created_at']
    list_filter = ['transaction_type', 'category', 'date']
    search_fields = ['description']

    


