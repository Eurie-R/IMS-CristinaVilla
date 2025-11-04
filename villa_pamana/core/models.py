from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class InventoryItem(models.Model):
    CATEGORY_CHOICES = [
        ('kitchen', 'Kitchen'),
        ('housekeeping', 'Housekeeping'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    quantity = models.PositiveIntegerField()
    minimum_stock = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
    
    def needs_restock(self):
        return self.quantity <= self.minimum_stock
    
class TodoTask(models.Model):

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='low')
    is_completed = models.BooleanField(default=False)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-priority', 'due_date']


class Booking(models.Model):
    ROOM_CHOICES = [
        ('1', 'Room 1'),
        ('2', 'Room 2'),
        ('3', 'Room 3'),
        ('4', 'Room 4'),
    ]


    guest_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    room_number = models.CharField(max_length=10, choices=ROOM_CHOICES  )
    number_of_guests = models.PositiveIntegerField()
    check_in = models.DateField()
    check_out = models.DateField()
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('pending', 'Pending'), ('cancelled', 'Cancelled')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking for {self.guest_name} in room {self.room_number}"
    
    def duration(self):
        return (self.check_out - self.check_in).days

class FinancialTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]

    CATEGORY_CHOICES = [
        ('booking', 'Booking Revenue'),
        ('maintenance', 'Maintenance Cost'),
        ('utilities', 'Utilities Cost'),
        ('salary', 'Salary Expense'),
        ('supplies', 'Supplies Cost'),
        ('other', 'Other'),
    ]

    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} - {self.category} - {self.amount}"
    
    class Meta:
        ordering = ['-date']
