from django.urls import path
from . import views

urlpatterns = [
    #Dashboard
    path('', views.dashboard, name='dashboard'),

    #Financials
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.inventory_add, name='inventory_add'),
    path('inventory/update/<int:item_id>/', views.inventory_update, name='inventory_update'),

    #To-Do Tasks
    path('todo/', views.todo_list, name='todo_list'),
    path('todo/add/', views.todo_add, name='todo_add'),
    path('todo/toggle/<int:task_id>/', views.todo_toggle, name='todo_toggle'),
    path('todo/delete/<int:task_id>/', views.todo_delete, name='todo_delete'),


    #Bookings
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/add/', views.booking_add, name='booking_add'),

    #Financial Transactions
    path('financials/', views.financial_summary, name='financial_list'),
    path('financials/add/', views.financial_add, name='financial_add'),
    path('financial/delete/<int:pk>/', views.financial_delete, name='financial_delete'),
]

