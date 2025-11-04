from django.shortcuts import render

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    InventoryCategory, InventoryItem, Task, Room, Booking,
    FinancialCategory, Transaction, CalendarEvent
)
from .serializers import (
    InventoryCategorySerializer, InventoryItemSerializer, TaskSerializer,
    RoomSerializer, BookingSerializer, BookingCreateSerializer,
    FinancialCategorySerializer, TransactionSerializer,
    CalendarEventSerializer, DashboardSerializer, UserSerializer
)

# Custom permission classes
class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

class IsStaffOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ['admin', 'staff']

class IsAccountantOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ['admin', 'accountant']

# Inventory ViewSets
class InventoryCategoryViewSet(viewsets.ModelViewSet):
    queryset = InventoryCategory.objects.all()
    serializer_class = InventoryCategorySerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

class InventoryItemViewSet(viewsets.ModelViewSet):
    queryset = InventoryItem.objects.select_related('category').all()
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_items = [item for item in self.queryset if item.needs_restock]
        serializer = self.get_serializer(low_stock_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def restock(self, request, pk=None):
        item = self.get_object()
        quantity = request.data.get('quantity', 0)
        
        if quantity <= 0:
            return Response(
                {'error': 'Quantity must be greater than 0'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        item.quantity += int(quantity)
        item.last_restocked = timezone.now()
        item.save()
        
        serializer = self.get_serializer(item)
        return Response(serializer.data)

# Task ViewSet
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.select_related('assigned_to').all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        status_filter = self.request.query_params.get('status', None)
        date_filter = self.request.query_params.get('date', None)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if date_filter:
            queryset = queryset.filter(due_date=date_filter)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)

# Room ViewSet
class RoomViewSet(viewsets.ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    
    @action(detail=False, methods=['get'])
    def availability(self, request):
        check_in = request.query_params.get('check_in')
        check_out = request.query_params.get('check_out')
        
        if not check_in or not check_out:
            return Response(
                {'error': 'check_in and check_out dates are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booked_rooms = Booking.objects.filter(
            status__in=['pending', 'confirmed', 'checked_in'],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        ).values_list('room_id', flat=True)
        
        available_rooms = Room.objects.exclude(id__in=booked_rooms).filter(status='available')
        serializer = self.get_serializer(available_rooms, many=True)
        return Response(serializer.data)

# Booking ViewSet
class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.select_related('room', 'created_by').all()
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BookingCreateSerializer
        return BookingSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'checked_in'
        booking.actual_check_in = timezone.now()
        booking.room.status = 'occupied'
        booking.room.save()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'checked_out'
        booking.actual_check_out = timezone.now()
        booking.room.status = 'available'
        booking.room.save()
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def calendar_view(self, request):
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if start_date and end_date:
            bookings = self.queryset.filter(
                Q(check_in_date__range=[start_date, end_date]) |
                Q(check_out_date__range=[start_date, end_date])
            )
        else:
            bookings = self.queryset
        
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

# Financial ViewSets
class FinancialCategoryViewSet(viewsets.ModelViewSet):
    queryset = FinancialCategory.objects.all()
    serializer_class = FinancialCategorySerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAdmin]

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.select_related('category', 'booking', 'recorded_by').all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsAccountantOrAdmin]
    
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        year = request.query_params.get('year', timezone.now().year)
        month = request.query_params.get('month', timezone.now().month)
        
        income = Transaction.objects.filter(
            transaction_type='income',
            date__year=year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Transaction.objects.filter(
            transaction_type='expense',
            date__year=year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'income': income,
            'expenses': expenses,
            'profit': income - expenses,
            'year': year,
            'month': month
        })
    
    @action(detail=False, methods=['get'])
    def monthly_breakdown(self, request):
        year = request.query_params.get('year', timezone.now().year)
        
        months_data = []
        for month in range(1, 13):
            income = Transaction.objects.filter(
                transaction_type='income',
                date__year=year,
                date__month=month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            expenses = Transaction.objects.filter(
                transaction_type='expense',
                date__year=year,
                date__month=month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            months_data.append({
                'month': month,
                'income': float(income),
                'expenses': float(expenses),
                'profit': float(income - expenses)
            })
        
        return Response(months_data)

# Calendar ViewSet
class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.select_related('created_by', 'related_booking').all()
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        
        if start and end:
            queryset = queryset.filter(
                start_datetime__range=[start, end]
            )
        
        return queryset

# Dashboard View
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request):
    today = timezone.now().date()
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    # Daily tasks
    daily_tasks = Task.objects.filter(
        due_date=today,
        status='pending'
    )[:10]
    
    # Restock alerts
    restock_alerts = [item for item in InventoryItem.objects.all() if item.needs_restock][:10]
    
    # Monthly financials
    monthly_income = Transaction.objects.filter(
        transaction_type='income',
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_expenses = Transaction.objects.filter(
        transaction_type='expense',
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Today's check-ins and check-outs
    todays_checkins = Booking.objects.filter(check_in_date=today, status='confirmed')
    todays_checkouts = Booking.objects.filter(check_out_date=today, status='checked_in')
    
    # Room statistics
    available_rooms = Room.objects.filter(status='available').count()
    occupied_rooms = Room.objects.filter(status='occupied').count()
    
    data = {
        'daily_tasks': TaskSerializer(daily_tasks, many=True).data,
        'restock_alerts': InventoryItemSerializer(restock_alerts, many=True).data,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_profit': monthly_income - monthly_expenses,
        'todays_checkins': BookingSerializer(todays_checkins, many=True).data,
        'todays_checkouts': BookingSerializer(todays_checkouts, many=True).data,
        'available_rooms': available_rooms,
        'occupied_rooms': occupied_rooms,
    }
    
    return Response(data)