from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, F
from datetime import date, timedelta
from .models import InventoryItem, TodoTask, Booking, FinancialTransaction

# Create your views here.

#Dashboard View
def dashboard(request):
    """
    Main Landing Page - Overview of everything 

    Content 
    1. Today's Tasks 
    2. Gets items that needs restocking 
    3. Calculates monthly financial summary
    4. Passes all data to dashboard template
    """

    today = date.today()

    # Get incomplete tasks for today or overdue 
    # Q object to handle OR condition using "|"

    tasks = TodoTask.objects.filter(
        Q(due_date=today) | Q(due_date__lt=today),
        is_completed=False
    ).order_by('-priority', 'due_date')

    # Get inventory items that need restocking
    restock_items = InventoryItem.objects.filter(
        quantity__lte=F('minimum_stock'))
    
    # Calculate monthly financial summary
    first_day_of_month = today.replace(day=1)

    monthly_income = FinancialTransaction.objects.filter(
        transaction_type='income',
        date__gte=first_day_of_month,
        date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_expenses = FinancialTransaction.objects.filter(
        transaction_type='expense',
        date__gte=first_day_of_month,
        date__lte=today
    ).aggregate(total=Sum('amount'))['total'] or 0

    monthly_profit = monthly_income - monthly_expenses

    #get Today's Bookings (check-in)
    todays_checkins = Booking.objects.filter(check_in=today)

    #prepare context
    context = {
        'tasks': tasks,
        'restock_items': restock_items,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_profit': monthly_profit,
        'todays_checkins': todays_checkins,
        'today' : today,
    }

    return render(request, 'core/dashboard.html', context)

def inventory_list(request):
    items = InventoryItem.objects.all().order_by('category', 'name')
    return render(request, 'core/inventory_list.html', {'items': items})

def inventory_add(request):
    # Logic for adding inventory item
    if request.method == 'POST':
        #get data from form 
        name = request.POST.get('name')
        category = request.POST.get('category')
        quantity = request.POST.get('quantity')
        minimum_stock = request.POST.get('minimum_stock')
        unit = request.POST.get('unit')

        #create new Item 
        InventoryItem.objects.create(
            name=name,
            category=category,
            quantity=quantity,
            minimum_stock=minimum_stock,
            unit=unit
        )

        messages.success(request, 'Inventory item added successfully.')
        return redirect('inventory_list')
    
    return render(request, 'core/inventory_add.html')

def inventory_update(request, item_id):
    item = get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        amount = int(request.POST.get('amount', 0))

        if action == 'add':
            item.quantity += amount
        elif action == 'remove':
            item.quantity -= amount 

        item.save()
        messages.success(request, 'Inventory item updated successfully.')
        return redirect('inventory_list')
    return redirect('inventory_list')

def todo_list(request):
    tasks = TodoTask.objects.all().order_by('-priority', 'due_date')

    #Seperate incomplete vs complete
    incomplete_tasks = tasks.filter(is_completed=False)
    completed_tasks = tasks.filter(is_completed=True)

    context={
        'incomplete_tasks': incomplete_tasks,
        'completed_tasks': completed_tasks,
    }

    return render(request, 'core/todo_list.html', context)

def todo_add(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        due_date = request.POST.get('due_date')

        TodoTask.objects.create(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date
        )

        messages.success(request, 'To-Do task added successfully.')
        return redirect('todo_list')
    return redirect('todo_list')

def todo_toggle(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)
    task.is_completed = not task.is_completed
    task.save()

    status = 'completed' if task.completed else 'reopened'
    messages.success(request, f'Task {status}!')
    return redirect('todo_list')

def todo_delete(request, task_id):
    task = get_object_or_404(TodoTask, id=task_id)
    task.delete()
    messages.success(request, 'Task deleted successfully.')
    return redirect('todo_list')

def booking_list(request):
    bookings = Booking.objects.all().order_by('-check_in')

    #Upcoming bookings 
    today = date.today()
    upcoming = bookings.filter(check_out__gte=today)
    past = bookings.filter(check_out__lt=today)

    context = {
        'upcoming_bookings': upcoming,
        'past_bookings': past,
    }
    return render(request, 'core/booking_list.html', context)

def booking_add(request):
    if request.method == 'POST':
        Booking.objects.create(
            guest_name=request.POST.get('guest_name'),
            contact_number=request.POST.get('contact_number'),
            room_number=request.POST.get('room_number'),
            number_of_guests=request.POST.get('number_of_guests'),
            check_in=request.POST.get('check_in'),
            check_out=request.POST.get('check_out'),
            payment_amount=request.POST.get('payment_amount'),
            payment_status=request.POST.get('payment_status'),
        )
        messages.success(request, 'Booking added successfully.')
        return redirect('booking_list')
    return redirect('booking_list')

def financial_summary(request):
    transactions = FinancialTransaction.objects.all().order_by('-date')

    #Calculate totals
    total_income = transactions.filter(
        transaction_type='income').aggregate(total=Sum('amount'))['total'] or 0

    total_expenses = transactions.filter(
        transaction_type='expense').aggregate(total=Sum('amount'))['total'] or 0

    net_profit = total_income - total_expenses

    context = {
        'transactions': transactions,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
    }

    return render(request, 'core/financial.html', context)

def financial_add(request):
    if request.method == 'POST':
        FinancialTransaction.objects.create(
            transaction_type=request.POST.get('transaction_type'),
            category=request.POST.get('category'),
            amount=request.POST.get('amount'),
            description=request.POST.get('description'),
            date=request.POST.get('date'),
        )
        messages.success(request, 'Financial transaction added successfully.')
        return redirect('financial_list')
    return redirect('financial_list')