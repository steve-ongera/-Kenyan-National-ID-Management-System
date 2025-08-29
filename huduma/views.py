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
    ).order_by('-created_at')[:4]
    
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



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.forms import model_to_dict
from decimal import Decimal
import json

from .models import (
    IDApplication, CustomUser, BirthCertificate, County, SubCounty, 
    Division, Location, SubLocation, Village, ChiefOffice, DOOffice,
    HudumaCentre, DocumentType, Document, ApplicationDocument,
    ApplicationStatusHistory
)


@login_required
def id_applications_list(request):
    """List all ID applications with search, filter, and pagination"""
    applications = IDApplication.objects.select_related(
        'applicant', 'birth_certificate', 'county_of_birth', 'current_county',
        'chief_office', 'do_office', 'huduma_centre'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        applications = applications.filter(
            Q(application_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(applicant__username__icontains=search_query) |
            Q(applicant__phone_number__icontains=search_query) |
            Q(birth_certificate__certificate_number__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Filter by application type
    type_filter = request.GET.get('type', '')
    if type_filter:
        applications = applications.filter(application_type=type_filter)
    
    # Filter by entry point
    entry_filter = request.GET.get('entry', '')
    if entry_filter:
        applications = applications.filter(entry_point=entry_filter)
    
    # Filter by county
    county_filter = request.GET.get('county', '')
    if county_filter:
        applications = applications.filter(current_county_id=county_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        applications = applications.filter(created_at__date__gte=date_from)
    if date_to:
        applications = applications.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(applications, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for dropdowns
    status_choices = IDApplication.APPLICATION_STATUS
    type_choices = IDApplication.APPLICATION_TYPES
    entry_choices = IDApplication.ENTRY_POINTS
    counties = County.objects.all().order_by('name')
    
    context = {
        'applications': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'entry_filter': entry_filter,
        'county_filter': county_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': status_choices,
        'type_choices': type_choices,
        'entry_choices': entry_choices,
        'counties': counties,
    }
    
    return render(request, 'id_applications/list.html', context)


@login_required
def id_application_detail(request, application_id):
    """View detailed information about a specific ID application"""
    application = get_object_or_404(
        IDApplication.objects.select_related(
            'applicant', 'birth_certificate', 'county_of_birth', 'current_county',
            'chief_office', 'do_office', 'huduma_centre', 'chief', 'do_officer'
        ).prefetch_related(
            'application_documents__document',
            'status_history',
            'notifications',
            'payments'
        ),
        application_id=application_id
    )
    
    # Get application documents
    app_documents = application.application_documents.select_related('document', 'document_type')
    
    # Get status history
    status_history = application.status_history.select_related('changed_by').order_by('-timestamp')
    
    # Get notifications
    notifications = application.notifications.order_by('-created_at')
    
    # Get payments
    payments = application.payments.select_related('fee').order_by('-created_at')
    
    context = {
        'application': application,
        'app_documents': app_documents,
        'status_history': status_history,
        'notifications': notifications,
        'payments': payments,
    }
    
    return render(request, 'id_applications/detail.html', context)


@login_required
def id_application_create(request):
    """Create a new ID application"""
    if request.method == 'POST':
        try:
            # Get birth certificate
            cert_number = request.POST.get('birth_certificate')
            birth_certificate = get_object_or_404(BirthCertificate, certificate_number=cert_number)
            
            # Create application
            application = IDApplication.objects.create(
                applicant=request.user,
                birth_certificate=birth_certificate,
                application_type=request.POST.get('application_type', 'new'),
                entry_point=request.POST.get('entry_point', 'online'),
                full_name=request.POST.get('full_name'),
                date_of_birth=request.POST.get('date_of_birth'),
                place_of_birth=request.POST.get('place_of_birth'),
                gender=request.POST.get('gender'),
                
                # Birth location
                county_of_birth_id=request.POST.get('county_of_birth'),
                sub_county_of_birth_id=request.POST.get('sub_county_of_birth'),
                division_of_birth_id=request.POST.get('division_of_birth'),
                location_of_birth_id=request.POST.get('location_of_birth'),
                sub_location_of_birth_id=request.POST.get('sub_location_of_birth'),
                village_of_birth_id=request.POST.get('village_of_birth'),
                
                # Current address
                current_county_id=request.POST.get('current_county'),
                current_sub_county_id=request.POST.get('current_sub_county'),
                current_division_id=request.POST.get('current_division'),
                current_location_id=request.POST.get('current_location'),
                current_sub_location_id=request.POST.get('current_sub_location'),
                current_village_id=request.POST.get('current_village'),
                
                # Family info
                clan_name=request.POST.get('clan_name'),
                father_name=request.POST.get('father_name'),
                father_id=request.POST.get('father_id'),
                mother_name=request.POST.get('mother_name'),
                mother_id=request.POST.get('mother_id'),
                guardian_name=request.POST.get('guardian_name'),
                guardian_id=request.POST.get('guardian_id'),
                guardian_relationship=request.POST.get('guardian_relationship'),
                
                # Contact info
                phone_number=request.POST.get('phone_number'),
                alternative_phone=request.POST.get('alternative_phone'),
                email=request.POST.get('email'),
                postal_address=request.POST.get('postal_address'),
                
                # For replacements
                previous_id_number=request.POST.get('previous_id_number'),
                police_ob_number=request.POST.get('police_ob_number'),
                police_station=request.POST.get('police_station'),
                replacement_reason=request.POST.get('replacement_reason'),
                
                # For name changes
                old_name=request.POST.get('old_name'),
                new_name=request.POST.get('new_name'),
                name_change_reason=request.POST.get('name_change_reason'),
            )
            
            # Create status history entry
            ApplicationStatusHistory.objects.create(
                application=application,
                previous_status=None,
                new_status='started',
                changed_by=request.user,
                change_reason='Application created',
                location_type='online'
            )
            
            messages.success(request, f'ID Application {application.application_number} created successfully!')
            return redirect('applications_detail', application_id=application.application_id)
            
        except Exception as e:
            messages.error(request, f'Error creating application: {str(e)}')
    
    # Get data for form dropdowns
    counties = County.objects.all().order_by('name')
    birth_certificates = BirthCertificate.objects.filter(is_active=True).order_by('full_name')
    
    context = {
        'counties': counties,
        'birth_certificates': birth_certificates,
        'application_types': IDApplication.APPLICATION_TYPES,
        'entry_points': IDApplication.ENTRY_POINTS,
        'replacement_reasons': IDApplication.REPLACEMENT_REASONS,
    }
    
    return render(request, 'id_applications/create.html', context)


@login_required
def id_application_update(request, application_id):
    """Update an existing ID application"""
    application = get_object_or_404(IDApplication, application_id=application_id)
    
    if request.method == 'POST':
        try:
            # Store original values for change tracking
            original_data = {
                'full_name': application.full_name,
                'phone_number': application.phone_number,
                'email': application.email,
            }
            
            # Update application fields
            application.full_name = request.POST.get('full_name')
            application.phone_number = request.POST.get('phone_number')
            application.alternative_phone = request.POST.get('alternative_phone')
            application.email = request.POST.get('email')
            application.postal_address = request.POST.get('postal_address')
            
            # Update current address
            application.current_county_id = request.POST.get('current_county')
            application.current_sub_county_id = request.POST.get('current_sub_county')
            application.current_division_id = request.POST.get('current_division')
            application.current_location_id = request.POST.get('current_location')
            application.current_sub_location_id = request.POST.get('current_sub_location')
            application.current_village_id = request.POST.get('current_village')
            
            # Update family info
            application.clan_name = request.POST.get('clan_name')
            application.father_name = request.POST.get('father_name')
            application.father_id = request.POST.get('father_id')
            application.mother_name = request.POST.get('mother_name')
            application.mother_id = request.POST.get('mother_id')
            application.guardian_name = request.POST.get('guardian_name')
            application.guardian_id = request.POST.get('guardian_id')
            application.guardian_relationship = request.POST.get('guardian_relationship')
            
            application.save()
            
            # Create status history entry for update
            changes = []
            if original_data['full_name'] != application.full_name:
                changes.append(f"Name changed from '{original_data['full_name']}' to '{application.full_name}'")
            if original_data['phone_number'] != application.phone_number:
                changes.append(f"Phone changed from '{original_data['phone_number']}' to '{application.phone_number}'")
            if original_data['email'] != application.email:
                changes.append(f"Email changed from '{original_data['email']}' to '{application.email}'")
            
            if changes:
                ApplicationStatusHistory.objects.create(
                    application=application,
                    previous_status=application.status,
                    new_status=application.status,
                    changed_by=request.user,
                    change_reason='Application updated',
                    notes='; '.join(changes),
                    location_type='online'
                )
            
            messages.success(request, 'Application updated successfully!')
            return redirect('applications_detail', application_id=application.application_id)
                
        except Exception as e:
            messages.error(request, f'Error updating application: {str(e)}')
    
    # Get data for form dropdowns
    counties = County.objects.all().order_by('name')
    sub_counties = SubCounty.objects.filter(county=application.current_county).order_by('name') if application.current_county else []
    divisions = Division.objects.filter(sub_county=application.current_sub_county).order_by('name') if application.current_sub_county else []
    locations = Location.objects.filter(division=application.current_division).order_by('name') if application.current_division else []
    sub_locations = SubLocation.objects.filter(location=application.current_location).order_by('name') if application.current_location else []
    villages = Village.objects.filter(sub_location=application.current_sub_location).order_by('name') if application.current_sub_location else []
    
    context = {
        'application': application,
        'counties': counties,
        'sub_counties': sub_counties,
        'divisions': divisions,
        'locations': locations,
        'sub_locations': sub_locations,
        'villages': villages,
    }
    
    return render(request, 'id_applications/update.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def id_application_delete(request, application_id):
    """Delete an ID application"""
    application = get_object_or_404(IDApplication, application_id=application_id)
    
    if request.method == 'POST':
        try:
            app_number = application.application_number
            app_name = application.full_name
            
            # Create final status history entry
            ApplicationStatusHistory.objects.create(
                application=application,
                previous_status=application.status,
                new_status='cancelled',
                changed_by=request.user,
                change_reason='Application deleted by user',
                location_type='online'
            )
            
            application.delete()
            messages.success(request, f'Application {app_number} for {app_name} has been deleted successfully!')
            return redirect('applications_list')
                
        except Exception as e:
            messages.error(request, f'Error deleting application: {str(e)}')
            return redirect('applications_detail', application_id=application_id)
    
    # GET request - show confirmation page
    context = {
        'application': application,
    }
    
    return render(request, 'id_applications/delete.html', context)


@login_required
def id_application_api_detail(request, application_id):
    """API endpoint to get application details for AJAX requests"""
    try:
        application = get_object_or_404(
            IDApplication.objects.select_related(
                'applicant', 'birth_certificate', 'county_of_birth', 'current_county',
                'chief_office', 'do_office', 'huduma_centre'
            ),
            application_id=application_id
        )
        
        data = {
            'application_number': application.application_number,
            'full_name': application.full_name,
            'application_type': application.get_application_type_display(),
            'application_type_code': application.application_type,
            'status': application.get_status_display(),
            'status_code': application.status,
            'entry_point': application.get_entry_point_display(),
            'entry_point_code': application.entry_point,
            'date_of_birth': application.date_of_birth.strftime('%B %d, %Y'),
            'dob_iso': application.date_of_birth.strftime('%Y-%m-%d'),
            'place_of_birth': application.place_of_birth,
            'gender': application.get_gender_display(),
            'gender_code': application.gender,
            'phone_number': application.phone_number,
            'alternative_phone': application.alternative_phone or 'N/A',
            'email': application.email or 'No email provided',
            'postal_address': application.postal_address or 'No address provided',
            'birth_certificate': application.birth_certificate.certificate_number,
            'county_of_birth': application.county_of_birth.name,
            'current_county': application.current_county.name,
            'clan_name': application.clan_name or 'Not specified',
            'father_name': application.father_name or 'Not provided',
            'father_id': application.father_id or 'Not provided',
            'mother_name': application.mother_name or 'Not provided',
            'mother_id': application.mother_id or 'Not provided',
            'guardian_name': application.guardian_name or 'Not applicable',
            'guardian_id': application.guardian_id or 'Not applicable',
            'guardian_relationship': application.guardian_relationship or 'Not applicable',
            'created_at': application.created_at.strftime('%B %d, %Y at %I:%M %p'),
            'updated_at': application.updated_at.strftime('%B %d, %Y at %I:%M %p'),
            'current_county_id': application.current_county_id,
            'current_sub_county_id': application.current_sub_county_id,
            'current_division_id': application.current_division_id,
            'current_location_id': application.current_location_id,
            'current_sub_location_id': application.current_sub_location_id,
            'current_village_id': application.current_village_id,
        }
        
        # Add replacement-specific data
        if application.application_type == 'replacement':
            data.update({
                'previous_id_number': application.previous_id_number or 'Not provided',
                'police_ob_number': application.police_ob_number or 'Not provided',
                'police_station': application.police_station or 'Not provided',
                'replacement_reason': application.get_replacement_reason_display() if application.replacement_reason else 'Not specified',
                'replacement_fee': str(application.replacement_fee),
                'fee_paid': application.fee_paid,
            })
        
        # Add name change-specific data
        if application.application_type == 'name_change':
            data.update({
                'old_name': application.old_name or 'Not provided',
                'new_name': application.new_name or 'Not provided',
                'name_change_reason': application.name_change_reason or 'Not provided',
            })
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error fetching application data: {str(e)}'
        }, status=500)


# Location API endpoints for cascading dropdowns (keep these as AJAX)
@login_required
def get_sub_counties(request, county_id):
    """Get sub-counties for a given county"""
    sub_counties = SubCounty.objects.filter(county_id=county_id).order_by('name')
    data = [{'id': sc.id, 'name': sc.name} for sc in sub_counties]
    return JsonResponse(data, safe=False)


@login_required
def get_divisions(request, sub_county_id):
    """Get divisions for a given sub-county"""
    divisions = Division.objects.filter(sub_county_id=sub_county_id).order_by('name')
    data = [{'id': d.id, 'name': d.name} for d in divisions]
    return JsonResponse(data, safe=False)


@login_required
def get_locations(request, division_id):
    """Get locations for a given division"""
    locations = Location.objects.filter(division_id=division_id).order_by('name')
    data = [{'id': l.id, 'name': l.name} for l in locations]
    return JsonResponse(data, safe=False)


@login_required
def get_sub_locations(request, location_id):
    """Get sub-locations for a given location"""
    sub_locations = SubLocation.objects.filter(location_id=location_id).order_by('name')
    data = [{'id': sl.id, 'name': sl.name} for sl in sub_locations]
    return JsonResponse(data, safe=False)


@login_required
def get_villages(request, sub_location_id):
    """Get villages for a given sub-location"""
    villages = Village.objects.filter(sub_location_id=sub_location_id).order_by('name')
    data = [{'id': v.id, 'name': v.name} for v in villages]
    return JsonResponse(data, safe=False)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import (
    BirthCertificate, County, SubCounty, Division, 
    Location, SubLocation, Village
)
from .forms import BirthCertificateForm
import json


@login_required
def birth_certificates_list(request):
    """List all birth certificates with filtering and search"""
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    county_filter = request.GET.get('county', '')
    sub_county_filter = request.GET.get('sub_county', '')
    gender_filter = request.GET.get('gender', '')
    nationality_filter = request.GET.get('nationality', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    is_active_filter = request.GET.get('is_active', '')
    is_verified_filter = request.GET.get('is_verified', '')
    
    # Base queryset
    certificates = BirthCertificate.objects.select_related(
        'county_of_birth', 'sub_county_of_birth', 'division_of_birth',
        'location_of_birth', 'sub_location_of_birth', 'village_of_birth'
    ).order_by('-created_at')
    
    # Apply filters
    if search_query:
        certificates = certificates.filter(
            Q(certificate_number__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mother_name__icontains=search_query) |
            Q(father_id__icontains=search_query) |
            Q(mother_id__icontains=search_query)
        )
    
    if county_filter:
        certificates = certificates.filter(county_of_birth_id=county_filter)
    
    if sub_county_filter:
        certificates = certificates.filter(sub_county_of_birth_id=sub_county_filter)
    
    if gender_filter:
        certificates = certificates.filter(gender=gender_filter)
    
    if nationality_filter:
        if nationality_filter == 'kenyan':
            certificates = certificates.filter(
                Q(father_nationality__iexact='KENYAN') | 
                Q(mother_nationality__iexact='KENYAN')
            )
        else:
            certificates = certificates.filter(
                ~Q(father_nationality__iexact='KENYAN') & 
                ~Q(mother_nationality__iexact='KENYAN')
            )
    
    if date_from:
        certificates = certificates.filter(date_of_birth__gte=date_from)
    
    if date_to:
        certificates = certificates.filter(date_of_birth__lte=date_to)
    
    if is_active_filter:
        certificates = certificates.filter(is_active=is_active_filter == 'true')
    
    if is_verified_filter:
        certificates = certificates.filter(is_verified=is_verified_filter == 'true')
    
    # Pagination
    paginator = Paginator(certificates, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter choices
    counties = County.objects.all().order_by('name')
    sub_counties = SubCounty.objects.all().order_by('name')
    
    if county_filter:
        sub_counties = sub_counties.filter(county_id=county_filter)
    
    gender_choices = [('M', 'Male'), ('F', 'Female')]
    nationality_choices = [('kenyan', 'Kenyan'), ('non_kenyan', 'Non-Kenyan')]
    
    context = {
        'certificates': page_obj,
        'search_query': search_query,
        'county_filter': county_filter,
        'sub_county_filter': sub_county_filter,
        'gender_filter': gender_filter,
        'nationality_filter': nationality_filter,
        'date_from': date_from,
        'date_to': date_to,
        'is_active_filter': is_active_filter,
        'is_verified_filter': is_verified_filter,
        'counties': counties,
        'sub_counties': sub_counties,
        'gender_choices': gender_choices,
        'nationality_choices': nationality_choices,
    }
    
    return render(request, 'certificates/birth_certificates_list.html', context)


@login_required
def birth_certificate_detail(request, certificate_number):
    """View birth certificate details"""
    certificate = get_object_or_404(BirthCertificate, certificate_number=certificate_number)
    
    context = {
        'certificate': certificate,
    }
    
    return render(request, 'certificates/birth_certificate_detail.html', context)


@login_required
def birth_certificate_create(request):
    """Create new birth certificate"""
    if request.method == 'POST':
        form = BirthCertificateForm(request.POST)
        if form.is_valid():
            certificate = form.save()
            messages.success(request, f'Birth certificate {certificate.certificate_number} created successfully.')
            return redirect('birth_certificate_detail', certificate_number=certificate.certificate_number)
    else:
        form = BirthCertificateForm()
    
    context = {
        'form': form,
        'title': 'Create Birth Certificate',
        'button_text': 'Create Certificate',
    }
    
    return render(request, 'certificates/birth_certificate_form.html', context)


@login_required
def birth_certificate_update(request, certificate_number):
    """Update birth certificate"""
    certificate = get_object_or_404(BirthCertificate, certificate_number=certificate_number)
    
    if request.method == 'POST':
        form = BirthCertificateForm(request.POST, instance=certificate)
        if form.is_valid():
            form.save()
            messages.success(request, f'Birth certificate {certificate.certificate_number} updated successfully.')
            return redirect('birth_certificate_detail', certificate_number=certificate.certificate_number)
    else:
        form = BirthCertificateForm(instance=certificate)
    
    context = {
        'form': form,
        'certificate': certificate,
        'title': 'Update Birth Certificate',
        'button_text': 'Update Certificate',
    }
    
    return render(request, 'certificates/birth_certificate_form.html', context)


@login_required
@require_http_methods(["POST"])
def birth_certificate_delete(request, certificate_number):
    """Delete birth certificate"""
    certificate = get_object_or_404(BirthCertificate, certificate_number=certificate_number)
    
    # Check if certificate is being used in any applications
    if hasattr(certificate, 'idapplication_set') and certificate.idapplication_set.exists():
        messages.error(request, 'Cannot delete certificate. It is being used in ID applications.')
        return redirect('birth_certificate_detail', certificate_number=certificate.certificate_number)
    
    certificate_number_copy = certificate.certificate_number
    certificate.delete()
    messages.success(request, f'Birth certificate {certificate_number_copy} deleted successfully.')
    
    return redirect('birth_certificates_list')

# national_ids/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin

from .models import (
    NationalID, IDApplication, County, SubCounty, Division, 
    Location, SubLocation, Village, CustomUser, BirthCertificate
)
from .forms import NationalIDForm, NationalIDFilterForm


@login_required
def national_id_list(request):
    """List all National IDs with filtering and search"""
    national_ids = NationalID.objects.select_related(
        'application', 
        'application__county_of_birth',
        'application__sub_county_of_birth',
        'collection_location'
    ).all()
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    county_filter = request.GET.get('county', '')
    sub_county_filter = request.GET.get('sub_county', '')
    gender_filter = request.GET.get('gender', '')
    is_active_filter = request.GET.get('is_active', '')
    is_collected_filter = request.GET.get('is_collected', '')
    is_printed_filter = request.GET.get('is_printed', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Apply search filter
    if search_query:
        national_ids = national_ids.filter(
            Q(id_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(application__application_number__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(place_of_birth__icontains=search_query)
        )
    
    # Apply county filter
    if county_filter:
        national_ids = national_ids.filter(
            application__county_of_birth_id=county_filter
        )
    
    # Apply sub-county filter
    if sub_county_filter:
        national_ids = national_ids.filter(
            application__sub_county_of_birth_id=sub_county_filter
        )
    
    # Apply gender filter
    if gender_filter:
        national_ids = national_ids.filter(gender=gender_filter)
    
    # Apply active status filter
    if is_active_filter:
        is_active = is_active_filter.lower() == 'true'
        national_ids = national_ids.filter(is_active=is_active)
    
    # Apply collected status filter
    if is_collected_filter:
        is_collected = is_collected_filter.lower() == 'true'
        national_ids = national_ids.filter(is_collected=is_collected)
    
    # Apply printed status filter
    if is_printed_filter:
        is_printed = is_printed_filter.lower() == 'true'
        national_ids = national_ids.filter(is_printed=is_printed)
    
    # Apply date range filter
    if date_from:
        try:
            date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
            national_ids = national_ids.filter(date_of_birth__gte=date_from_parsed)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
            national_ids = national_ids.filter(date_of_birth__lte=date_to_parsed)
        except ValueError:
            pass
    
    # Order by most recent first
    national_ids = national_ids.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(national_ids, 25)  # Show 25 IDs per page
    page = request.GET.get('page')
    
    try:
        national_ids = paginator.page(page)
    except PageNotAnInteger:
        national_ids = paginator.page(1)
    except EmptyPage:
        national_ids = paginator.page(paginator.num_pages)
    
    # Get counties for filter dropdown
    counties = County.objects.all().order_by('name')
    
    # Get sub-counties based on selected county
    sub_counties = SubCounty.objects.all().order_by('name')
    if county_filter:
        sub_counties = sub_counties.filter(county_id=county_filter)
    
    # Gender choices
    gender_choices = [('M', 'Male'), ('F', 'Female')]
    
    context = {
        'national_ids': national_ids,
        'counties': counties,
        'sub_counties': sub_counties,
        'gender_choices': gender_choices,
        'search_query': search_query,
        'county_filter': county_filter,
        'sub_county_filter': sub_county_filter,
        'gender_filter': gender_filter,
        'is_active_filter': is_active_filter,
        'is_collected_filter': is_collected_filter,
        'is_printed_filter': is_printed_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'national_ids/list.html', context)


@login_required
def national_id_detail(request, id_number):
    """View National ID details"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    context = {
        'national_id': national_id,
        'application': national_id.application,
        'biometric_data': getattr(national_id.application, 'biometric_data', None),
        'waiting_card': getattr(national_id.application, 'waiting_card', None),
    }
    
    return render(request, 'national_ids/detail.html', context)


@login_required
def national_id_create(request):
    """Create a new National ID (Admin function)"""
    if request.method == 'POST':
        form = NationalIDForm(request.POST, request.FILES)
        if form.is_valid():
            national_id = form.save(commit=False)
            
            # Set additional fields
            national_id.place_of_issue = request.user.county.name if hasattr(request.user, 'county') and request.user.county else 'Nairobi'
            
            national_id.save()
            
            messages.success(request, f'National ID {national_id.id_number} created successfully for {national_id.full_name}.')
            return redirect('national_id_detail', id_number=national_id.id_number)
    else:
        form = NationalIDForm()
    
    context = {
        'form': form,
        'title': 'Create National ID',
        'submit_text': 'Create ID',
    }
    
    return render(request, 'national_ids/form.html', context)


@login_required
def national_id_update(request, id_number):
    """Update National ID details"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    if request.method == 'POST':
        form = NationalIDForm(request.POST, request.FILES, instance=national_id)
        if form.is_valid():
            form.save()
            messages.success(request, f'National ID {national_id.id_number} updated successfully.')
            return redirect('national_id_detail', id_number=national_id.id_number)
    else:
        form = NationalIDForm(instance=national_id)
    
    context = {
        'form': form,
        'national_id': national_id,
        'title': f'Update National ID - {national_id.id_number}',
        'submit_text': 'Update ID',
    }
    
    return render(request, 'national_ids/form.html', context)


@login_required
def national_id_delete(request, id_number):
    """Delete National ID"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    if request.method == 'POST':
        id_num = national_id.id_number
        full_name = national_id.full_name
        national_id.delete()
        messages.success(request, f'National ID {id_num} for {full_name} has been deleted successfully.')
        return redirect('national_id_list')
    
    context = {
        'national_id': national_id,
    }
    
    return render(request, 'national_ids/confirm_delete.html', context)


@login_required
def national_id_mark_collected(request, id_number):
    """Mark National ID as collected"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    if request.method == 'POST':
        if not national_id.is_collected:
            national_id.is_collected = True
            national_id.collected_at = timezone.now()
            national_id.collected_by = request.user
            national_id.save()
            
            # Update application status
            if hasattr(national_id, 'application'):
                national_id.application.status = 'collected'
                national_id.application.save()
            
            messages.success(request, f'National ID {national_id.id_number} marked as collected.')
        else:
            messages.info(request, f'National ID {national_id.id_number} is already marked as collected.')
    
    return redirect('national_id_detail', id_number=id_number)


@login_required
def national_id_mark_printed(request, id_number):
    """Mark National ID as printed"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    if request.method == 'POST':
        if not national_id.is_printed:
            national_id.is_printed = True
            national_id.printed_at = timezone.now()
            national_id.save()
            
            messages.success(request, f'National ID {national_id.id_number} marked as printed.')
        else:
            messages.info(request, f'National ID {national_id.id_number} is already marked as printed.')
    
    return redirect('national_id_detail', id_number=id_number)


@login_required
def national_id_mark_dispatched(request, id_number):
    """Mark National ID as dispatched"""
    national_id = get_object_or_404(NationalID, id_number=id_number)
    
    if request.method == 'POST':
        if not national_id.is_dispatched:
            national_id.is_dispatched = True
            national_id.dispatched_at = timezone.now()
            national_id.is_ready_for_collection = True
            national_id.save()
            
            # Update application status
            if hasattr(national_id, 'application'):
                national_id.application.status = 'ready_for_collection'
                national_id.application.save()
            
            messages.success(request, f'National ID {national_id.id_number} marked as dispatched and ready for collection.')
        else:
            messages.info(request, f'National ID {national_id.id_number} is already marked as dispatched.')
    
    return redirect('national_id_detail', id_number=id_number)


@login_required
def ajax_sub_counties(request):
    """AJAX view to get sub-counties for a county"""
    county_id = request.GET.get('county_id')
    sub_counties = []
    
    if county_id:
        sub_counties_qs = SubCounty.objects.filter(county_id=county_id).order_by('name')
        sub_counties = [{'id': sc.id, 'name': sc.name} for sc in sub_counties_qs]
    
    return JsonResponse({'sub_counties': sub_counties})


@login_required
def national_id_statistics(request):
    """Dashboard with National ID statistics"""
    stats = {
        'total_ids': NationalID.objects.count(),
        'active_ids': NationalID.objects.filter(is_active=True).count(),
        'collected_ids': NationalID.objects.filter(is_collected=True).count(),
        'pending_collection': NationalID.objects.filter(
            is_ready_for_collection=True, 
            is_collected=False
        ).count(),
        'printed_ids': NationalID.objects.filter(is_printed=True).count(),
        'dispatched_ids': NationalID.objects.filter(is_dispatched=True).count(),
    }
    
    # Recent IDs
    recent_ids = NationalID.objects.select_related('application').order_by('-created_at')[:10]
    
    # IDs by county
    from django.db.models import Count
    county_stats = NationalID.objects.select_related(
        'application__county_of_birth'
    ).values(
        'application__county_of_birth__name'
    ).annotate(
        count=Count('id_number')
    ).order_by('-count')[:10]
    
    context = {
        'stats': stats,
        'recent_ids': recent_ids,
        'county_stats': county_stats,
    }
    
    return render(request, 'national_ids/statistics.html', context)



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.forms import ModelForm, forms
from django import forms
from .models import (
    IDApplication, BirthCertificate, County, SubCounty, Division, 
    Location, SubLocation, Village, ChiefOffice, DOOffice, HudumaCentre,
    CustomUser
)


class ReplacementIDApplicationForm(ModelForm):
    class Meta:
        model = IDApplication
        fields = [
            'birth_certificate', 'full_name', 'date_of_birth', 'gender',
            'county_of_birth', 'sub_county_of_birth', 'division_of_birth',
            'location_of_birth', 'sub_location_of_birth', 'village_of_birth',
            'current_county', 'current_sub_county', 'current_division',
            'current_location', 'current_sub_location', 'current_village',
            'clan_name', 'father_name', 'father_id', 'mother_name', 'mother_id',
            'guardian_name', 'guardian_id', 'guardian_relationship',
            'phone_number', 'alternative_phone', 'email', 'postal_address',
            'previous_id_number', 'police_ob_number', 'police_station',
            'replacement_reason', 'replacement_fee', 'chief_office',
            'huduma_centre', 'entry_point'
        ]
        
        widgets = {
            'birth_certificate': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'county_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'sub_county_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'division_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'location_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'sub_location_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'village_of_birth': forms.Select(attrs={'class': 'form-select'}),
            'current_county': forms.Select(attrs={'class': 'form-select'}),
            'current_sub_county': forms.Select(attrs={'class': 'form-select'}),
            'current_division': forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.Select(attrs={'class': 'form-select'}),
            'current_sub_location': forms.Select(attrs={'class': 'form-select'}),
            'current_village': forms.Select(attrs={'class': 'form-select'}),
            'clan_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_id': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_id': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_id': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'postal_address': forms.TextInput(attrs={'class': 'form-control'}),
            'previous_id_number': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'police_ob_number': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'police_station': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'replacement_reason': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'replacement_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'chief_office': forms.Select(attrs={'class': 'form-select'}),
            'huduma_centre': forms.Select(attrs={'class': 'form-select'}),
            'entry_point': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_certificate'].queryset = BirthCertificate.objects.filter(is_active=True)
        self.fields['county_of_birth'].queryset = County.objects.all()
        self.fields['current_county'].queryset = County.objects.all()
        self.fields['chief_office'].queryset = ChiefOffice.objects.filter(is_active=True)
        self.fields['huduma_centre'].queryset = HudumaCentre.objects.filter(is_active=True)


@login_required
def replacement_id_list(request):
    """List all replacement ID applications with search and filtering"""
    applications = IDApplication.objects.filter(application_type='replacement').select_related(
        'applicant', 'birth_certificate', 'county_of_birth', 'sub_county_of_birth',
        'current_county', 'current_sub_county', 'chief_office', 'huduma_centre'
    ).order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        applications = applications.filter(
            Q(application_number__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(previous_id_number__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(police_ob_number__icontains=search_query) |
            Q(applicant__username__icontains=search_query)
        )
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    reason_filter = request.GET.get('replacement_reason')
    if reason_filter:
        applications = applications.filter(replacement_reason=reason_filter)
    
    county_filter = request.GET.get('county')
    if county_filter:
        applications = applications.filter(current_county_id=county_filter)
    
    entry_point_filter = request.GET.get('entry_point')
    if entry_point_filter:
        applications = applications.filter(entry_point=entry_point_filter)
    
    fee_paid_filter = request.GET.get('fee_paid')
    if fee_paid_filter:
        fee_paid_bool = fee_paid_filter == 'true'
        applications = applications.filter(fee_paid=fee_paid_bool)
    
    gender_filter = request.GET.get('gender')
    if gender_filter:
        applications = applications.filter(gender=gender_filter)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        applications = applications.filter(created_at__date__gte=date_from)
    if date_to:
        applications = applications.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    applications_page = paginator.get_page(page_number)
    
    # Get choices for filters
    status_choices = IDApplication.APPLICATION_STATUS
    reason_choices = IDApplication.REPLACEMENT_REASONS
    entry_point_choices = IDApplication.ENTRY_POINTS
    gender_choices = [('M', 'Male'), ('F', 'Female')]
    counties = County.objects.all()
    
    context = {
        'applications': applications_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'reason_filter': reason_filter,
        'county_filter': county_filter,
        'entry_point_filter': entry_point_filter,
        'fee_paid_filter': fee_paid_filter,
        'gender_filter': gender_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_choices': status_choices,
        'reason_choices': reason_choices,
        'entry_point_choices': entry_point_choices,
        'gender_choices': gender_choices,
        'counties': counties,
    }
    
    return render(request, 'replacements/replacement_list.html', context)


@login_required
def replacement_id_detail(request, application_id):
    """Detail view for replacement ID application"""
    application = get_object_or_404(
        IDApplication.objects.select_related(
            'applicant', 'birth_certificate', 'county_of_birth', 'sub_county_of_birth',
            'division_of_birth', 'location_of_birth', 'sub_location_of_birth', 'village_of_birth',
            'current_county', 'current_sub_county', 'current_division', 'current_location',
            'current_sub_location', 'current_village', 'chief_office', 'do_office', 'huduma_centre'
        ).prefetch_related('status_history', 'application_documents', 'notifications'),
        application_id=application_id,
        application_type='replacement'
    )
    
    context = {
        'application': application,
    }
    
    return render(request, 'replacements/replacement_detail.html', context)


@login_required
def replacement_id_create(request):
    """Create new replacement ID application"""
    if request.method == 'POST':
        form = ReplacementIDApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            application.application_type = 'replacement'
            application.status = 'started'
            application.save()
            
            messages.success(request, f'Replacement ID application {application.application_number} created successfully.')
            return redirect('replacement_id_detail', application_id=application.application_id)
    else:
        form = ReplacementIDApplicationForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'replacements/replacement_form.html', context)


@login_required
def replacement_id_update(request, application_id):
    """Update replacement ID application"""
    application = get_object_or_404(IDApplication, application_id=application_id, application_type='replacement')
    
    if request.method == 'POST':
        form = ReplacementIDApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, f'Replacement ID application {application.application_number} updated successfully.')
            return redirect('replacement_id_detail', application_id=application.application_id)
    else:
        form = ReplacementIDApplicationForm(instance=application)
    
    context = {
        'form': form,
        'application': application,
        'action': 'Update',
    }
    
    return render(request, 'replacements/replacement_form.html', context)


@login_required
@require_http_methods(["POST"])
def replacement_id_delete(request, application_id):
    """Delete replacement ID application"""
    application = get_object_or_404(IDApplication, application_id=application_id, application_type='replacement')
    application_number = application.application_number
    applicant_name = application.full_name
    
    application.delete()
    
    messages.success(request, f'Replacement ID application {application_number} for {applicant_name} has been deleted successfully.')
    return redirect('replacement_id_list')


# AJAX Views for cascading dropdowns
@login_required
def ajax_sub_counties(request):
    """Get sub-counties for a county via AJAX"""
    county_id = request.GET.get('county_id')
    sub_counties = SubCounty.objects.filter(county_id=county_id).values('id', 'name')
    return JsonResponse({'sub_counties': list(sub_counties)})


@login_required
def ajax_divisions(request):
    """Get divisions for a sub-county via AJAX"""
    sub_county_id = request.GET.get('sub_county_id')
    divisions = Division.objects.filter(sub_county_id=sub_county_id).values('id', 'name')
    return JsonResponse({'divisions': list(divisions)})


@login_required
def ajax_locations(request):
    """Get locations for a division via AJAX"""
    division_id = request.GET.get('division_id')
    locations = Location.objects.filter(division_id=division_id).values('id', 'name')
    return JsonResponse({'locations': list(locations)})


@login_required
def ajax_sub_locations(request):
    """Get sub-locations for a location via AJAX"""
    location_id = request.GET.get('location_id')
    sub_locations = SubLocation.objects.filter(location_id=location_id).values('id', 'name')
    return JsonResponse({'sub_locations': list(sub_locations)})


@login_required
def ajax_villages(request):
    """Get villages for a sub-location via AJAX"""
    sub_location_id = request.GET.get('sub_location_id')
    villages = Village.objects.filter(sub_location_id=sub_location_id).values('id', 'name')
    return JsonResponse({'villages': list(villages)})



# views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Q
from .models import BirthCertificate, County, SubCounty, Division, Location, SubLocation, Village
import time
import json


@staff_member_required
def birth_certificate_verify(request):
    """Main birth certificate verification page"""
    context = {
        'page_title': 'Birth Certificate Verification',
        'breadcrumbs': [
            {'name': 'Home', 'url': '/'},
            {'name': 'Birth Certificates', 'url': '/certificates/'},
            {'name': 'Verify Certificate', 'url': None}
        ]
    }
    return render(request, 'certificates/verify_certificate.html', context)


@csrf_exempt
@staff_member_required
def birth_certificate_search(request):
    """AJAX endpoint to search for birth certificate"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        certificate_number = data.get('certificate_number', '').strip()
        serial_number = data.get('serial_number', '').strip()
        
        # Simulate search delay with progress updates
        time.sleep(0.5)  # Simulate processing time
        
        if not certificate_number and not serial_number:
            return JsonResponse({
                'success': False,
                'error': 'Please provide at least one search parameter'
            })
        
        # Build search query
        query = Q()
        if certificate_number:
            query &= Q(certificate_number__iexact=certificate_number)
        if serial_number:
            query &= Q(serial_number__iexact=serial_number)
        
        # Search for certificate
        try:
            certificate = BirthCertificate.objects.select_related(
                'county_of_birth',
                'sub_county_of_birth', 
                'division_of_birth',
                'location_of_birth',
                'sub_location_of_birth',
                'village_of_birth'
            ).get(query)
            
            # Calculate age
            age = timezone.now().date().year - certificate.date_of_birth.year
            if (timezone.now().date().month, timezone.now().date().day) < (certificate.date_of_birth.month, certificate.date_of_birth.day):
                age -= 1
            
            certificate_data = {
                'success': True,
                'found': True,
                'certificate': {
                    'certificate_number': certificate.certificate_number,
                    'serial_number': certificate.serial_number,
                    'full_name': certificate.full_name,
                    'date_of_birth': certificate.date_of_birth.strftime('%d/%m/%Y'),
                    'age': age,
                    'place_of_birth': certificate.place_of_birth,
                    'gender': certificate.get_gender_display(),
                    'gender_code': certificate.gender,
                    
                    # Location hierarchy
                    'county_of_birth': certificate.county_of_birth.name,
                    'sub_county_of_birth': certificate.sub_county_of_birth.name,
                    'division_of_birth': certificate.division_of_birth.name,
                    'location_of_birth': certificate.location_of_birth.name,
                    'sub_location_of_birth': certificate.sub_location_of_birth.name,
                    'village_of_birth': certificate.village_of_birth.name,
                    
                    # Family information
                    'father_name': certificate.father_name or 'NOT INDICATED',
                    'father_id': certificate.father_id or 'NOT INDICATED',
                    'father_nationality': certificate.father_nationality,
                    'mother_name': certificate.mother_name or 'NOT INDICATED', 
                    'mother_id': certificate.mother_id or 'NOT INDICATED',
                    'mother_nationality': certificate.mother_nationality,
                    'guardian_name': certificate.guardian_name or 'N/A',
                    'guardian_id': certificate.guardian_id or 'N/A',
                    'guardian_relationship': certificate.guardian_relationship or 'N/A',
                    
                    # Registration details
                    'registration_date': certificate.registration_date.strftime('%d/%m/%Y'),
                    'issuing_office': certificate.issuing_office,
                    'registrar_name': certificate.registrar_name,
                    
                    # Status information
                    'is_active': certificate.is_active,
                    'is_verified': certificate.is_verified,
                    'is_kenyan_born': certificate.is_kenyan_born,
                    'naturalization_cert': certificate.naturalization_cert or 'N/A',
                    'citizenship_acquired_date': certificate.citizenship_acquired_date.strftime('%d/%m/%Y') if certificate.citizenship_acquired_date else 'N/A',
                    
                    # System dates
                    'created_at': certificate.created_at.strftime('%d/%m/%Y %H:%M'),
                    'updated_at': certificate.updated_at.strftime('%d/%m/%Y %H:%M'),
                }
            }
            
            return JsonResponse(certificate_data)
            
        except BirthCertificate.DoesNotExist:
            return JsonResponse({
                'success': True,
                'found': False,
                'message': 'No birth certificate found with the provided details'
            })
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        })


@staff_member_required
def birth_certificate_verify_status(request, certificate_number):
    """Update verification status of a birth certificate"""
    if request.method == 'POST':
        try:
            certificate = get_object_or_404(BirthCertificate, certificate_number=certificate_number)
            action = request.POST.get('action')
            
            if action == 'verify':
                certificate.is_verified = True
            elif action == 'unverify':
                certificate.is_verified = False
            elif action == 'deactivate':
                certificate.is_active = False
            elif action == 'activate':
                certificate.is_active = True
            
            certificate.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Certificate {action}d successfully',
                'new_status': {
                    'is_verified': certificate.is_verified,
                    'is_active': certificate.is_active
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@staff_member_required 
def birth_certificate_verification_log(request):
    """View verification history and logs"""
    # This would typically involve a separate model to track verification history
    # For now, just return recent certificates
    recent_certificates = BirthCertificate.objects.select_related(
        'county_of_birth'
    ).order_by('-updated_at')[:50]
    
    context = {
        'recent_certificates': recent_certificates,
        'page_title': 'Verification Log'
    }
    
    return render(request, 'certificates/verification_log.html', context)