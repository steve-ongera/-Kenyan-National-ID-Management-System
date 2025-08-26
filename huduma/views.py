# views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import (
    CustomUser, IDApplication, BirthCertificate, ChiefOffice, DOOffice, 
    HudumaCentre, Payment, Fee, ApplicationStatusHistory, County,
    BiometricAppointment, NationalID, Notification
)


def login_view(request):
    """Login view that redirects users to appropriate dashboards based on user type"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect based on user type
                    if user.user_type == 'admin':
                        return redirect('admin_dashboard')
                    elif user.user_type == 'chief':
                        return redirect('chief_dashboard')
                    elif user.user_type == 'chief_staff':
                        return redirect('chief_staff_dashboard')
                    elif user.user_type == 'do_officer':
                        return redirect('do_dashboard')
                    elif user.user_type == 'do_staff':
                        return redirect('do_staff_dashboard')
                    elif user.user_type == 'huduma_staff':
                        return redirect('huduma_dashboard')
                    else:  # mwananchi
                        return redirect('citizen_dashboard')
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact administrator.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please enter both username and password.')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Logout view"""
    user_name = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'You have been logged out successfully. Goodbye!')
    return redirect('login')


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user type"""
    user = request.user
    
    if user.user_type == 'admin':
        return redirect('admin_dashboard')
    elif user.user_type == 'chief':
        return redirect('chief_dashboard')
    elif user.user_type == 'chief_staff':
        return redirect('chief_staff_dashboard')
    elif user.user_type == 'do_officer':
        return redirect('do_dashboard')
    elif user.user_type == 'do_staff':
        return redirect('do_staff_dashboard')
    elif user.user_type == 'huduma_staff':
        return redirect('huduma_dashboard')
    else:  # mwananchi
        return redirect('citizen_dashboard')

@login_required
def admin_dashboard(request):
    """Admin dashboard with comprehensive statistics and charts"""
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    # Date ranges for filtering
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    current_month = today.replace(day=1)
    
    # Basic Statistics
    total_applications = IDApplication.objects.count()
    pending_applications = IDApplication.objects.filter(
        status__in=['started', 'documents_uploaded', 'chief_review', 'do_review']
    ).count()
    
    approved_applications = IDApplication.objects.filter(
        status__in=['do_approved', 'biometrics_scheduled', 'biometrics_taken', 'processing']
    ).count()
    
    completed_applications = IDApplication.objects.filter(
        status='collected'
    ).count()
    
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(date_joined__date=today).count()
    
    # Revenue Statistics
    total_revenue = Payment.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    monthly_revenue = Payment.objects.filter(
        status='completed',
        paid_at__date__gte=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Application Status Distribution for Pie Chart
    status_distribution = IDApplication.objects.values('status').annotate(
        count=Count('status')
    ).order_by('-count')
    
    status_labels = [item['status'].replace('_', ' ').title() for item in status_distribution]
    status_counts = [item['count'] for item in status_distribution]
    
    # Daily Applications Chart (Last 7 days)
    daily_applications = []
    daily_labels = []
    
    for i in range(6, -1, -1):  # Last 7 days
        date = today - timedelta(days=i)
        count = IDApplication.objects.filter(created_at__date=date).count()
        daily_applications.append(count)
        daily_labels.append(date.strftime('%m/%d'))
    
    # Monthly Applications Trend (Last 6 months)
    monthly_applications = []
    monthly_labels = []
    
    for i in range(5, -1, -1):  # Last 6 months
        date = today.replace(day=1) - timedelta(days=30*i)
        start_date = date.replace(day=1)
        if i == 0:
            end_date = today
        else:
            next_month = date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        
        count = IDApplication.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        monthly_applications.append(count)
        monthly_labels.append(date.strftime('%b %Y'))
    
    # County-wise Applications
    county_applications = IDApplication.objects.values(
        'current_county__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 counties
    
    county_labels = [item['current_county__name'] or 'Unknown' for item in county_applications]
    county_counts = [item['count'] for item in county_applications]
    
    # Application Type Distribution
    type_distribution = IDApplication.objects.values('application_type').annotate(
        count=Count('application_type')
    )
    
    type_labels = [item['application_type'].replace('_', ' ').title() for item in type_distribution]
    type_counts = [item['count'] for item in type_distribution]
    
    # Revenue Trend (Last 7 days)
    revenue_data = []
    revenue_labels = []
    
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        revenue = Payment.objects.filter(
            status='completed',
            paid_at__date=date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        revenue_data.append(float(revenue))
        revenue_labels.append(date.strftime('%m/%d'))
    
    # Processing Time Analysis - FIXED: Use NationalID.collected_at instead of IDApplication.collected_at
    completed_ids = NationalID.objects.select_related('application').filter(
        is_collected=True,
        collected_at__gte=timezone.now() - timedelta(days=30)
    )
    
    processing_times = []
    for national_id in completed_ids:
        if national_id.collected_at and national_id.application.created_at:
            days = (national_id.collected_at.date() - national_id.application.created_at.date()).days
            processing_times.append(days)
    
    avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
    
    # Recent Activities
    recent_applications = IDApplication.objects.select_related(
        'applicant', 'current_county'
    ).order_by('-created_at')[:10]
    
    recent_status_changes = ApplicationStatusHistory.objects.select_related(
        'application', 'changed_by'
    ).order_by('-timestamp')[:10]
    
    # System Health Metrics
    total_offices = ChiefOffice.objects.filter(is_active=True).count()
    total_do_offices = DOOffice.objects.filter(is_active=True).count()
    total_huduma_centres = HudumaCentre.objects.filter(is_active=True).count()
    
    # Alerts and Notifications
    pending_biometric_appointments = BiometricAppointment.objects.filter(
        is_confirmed=False,
        scheduled_date__date=today
    ).count()
    
    overdue_collections = NationalID.objects.filter(
        is_ready_for_collection=True,
        is_collected=False,
        date_of_issue__lt=today - timedelta(days=30)
    ).count()
    
    context = {
        # Basic Stats
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'completed_applications': completed_applications,
        'total_users': total_users,
        'new_users_today': new_users_today,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'avg_processing_time': round(avg_processing_time, 1),
        
        # Chart Data
        'status_labels': json.dumps(status_labels),
        'status_counts': json.dumps(status_counts),
        'daily_labels': json.dumps(daily_labels),
        'daily_applications': json.dumps(daily_applications),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_applications': json.dumps(monthly_applications),
        'county_labels': json.dumps(county_labels),
        'county_counts': json.dumps(county_counts),
        'type_labels': json.dumps(type_labels),
        'type_counts': json.dumps(type_counts),
        'revenue_labels': json.dumps(revenue_labels),
        'revenue_data': json.dumps(revenue_data),
        
        # Recent Activities
        'recent_applications': recent_applications,
        'recent_status_changes': recent_status_changes,
        
        # System Metrics
        'total_offices': total_offices,
        'total_do_offices': total_do_offices,
        'total_huduma_centres': total_huduma_centres,
        
        # Alerts
        'pending_biometric_appointments': pending_biometric_appointments,
        'overdue_collections': overdue_collections,
        
        # User info
        'user': request.user,
    }

    return render(request, 'dashboard/admin_dashboard.html', context)

# API endpoints for dashboard data updates
@login_required
def dashboard_api_stats(request):
    """API endpoint for real-time dashboard statistics"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    today = timezone.now().date()
    
    stats = {
        'total_applications': IDApplication.objects.count(),
        'pending_applications': IDApplication.objects.filter(
            status__in=['started', 'documents_uploaded', 'chief_review', 'do_review']
        ).count(),
        'completed_today': IDApplication.objects.filter(
            status='collected',
            updated_at__date=today
        ).count(),
        'revenue_today': float(Payment.objects.filter(
            status='completed',
            paid_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')),
        'new_users_today': CustomUser.objects.filter(
            date_joined__date=today
        ).count(),
    }
    
    return JsonResponse(stats)


@login_required 
def dashboard_api_applications_trend(request):
    """API endpoint for applications trend data"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    period = request.GET.get('period', '7')  # days
    days = int(period)
    today = timezone.now().date()
    
    trend_data = []
    labels = []
    
    for i in range(days-1, -1, -1):
        date = today - timedelta(days=i)
        count = IDApplication.objects.filter(created_at__date=date).count()
        trend_data.append(count)
        labels.append(date.strftime('%m/%d'))
    
    return JsonResponse({
        'labels': labels,
        'data': trend_data
    })


# Dashboard views for other user types
@login_required
def chief_dashboard(request):
    """Chief dashboard"""
    if request.user.user_type not in ['chief', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Chief-specific statistics
    if request.user.user_type == 'chief':
        chief_office = request.user.chief.office
        applications = IDApplication.objects.filter(chief_office=chief_office)
    else:  # admin viewing
        applications = IDApplication.objects.all()
    
    context = {
        'total_applications': applications.count(),
        'pending_review': applications.filter(status='chief_review').count(),
        'approved': applications.filter(status='chief_approved').count(),
        'user': request.user,
    }
    
    return render(request, 'dashboards/chief_dashboard.html', context)


@login_required
def do_dashboard(request):
    """DO Officer dashboard"""
    if request.user.user_type not in ['do_officer', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'dashboards/do_dashboard.html', context)


@login_required
def citizen_dashboard(request):
    """Citizen dashboard"""
    if request.user.user_type not in ['mwananchi', 'admin']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get user's applications
    applications = IDApplication.objects.filter(applicant=request.user)
    
    context = {
        'applications': applications,
        'total_applications': applications.count(),
        'user': request.user,
    }
    
    return render(request, 'dashboards/citizen_dashboard.html', context)