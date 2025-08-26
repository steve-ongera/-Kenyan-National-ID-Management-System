# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import qrcode
from io import BytesIO
import base64

from .models import (
    CustomUser, County, SubCounty, Division, Location, SubLocation, Village,
    ChiefOffice, Chief, ChiefStaff, DOOffice, DOOfficer, DOStaff,
    HudumaCentre, HudumaStaff, BirthCertificate, DocumentType, Document,
    IDApplication, ApplicationDocument, ChiefEligibilityLetter,
    BiometricAppointment, BiometricData, WaitingCard, NationalID,
    ApplicationStatusHistory, NotificationTemplate, Notification,
    Fee, Payment, SystemSettings, AuditLog, SecurityIncident, Report
)


# Custom Admin Site Configuration
class KenyanIDAdminSite(admin.AdminSite):
    site_header = "Kenyan National ID Management System"
    site_title = "Kenyan ID Admin"
    index_title = "System Administration Dashboard"


# User Management
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'phone_number', 'is_verified', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_active', 'county', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'national_id')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone_number', 'alternative_phone', 'national_id', 'is_verified', 'profile_photo')
        }),
        ('Location', {
            'fields': ('county', 'sub_county')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('county', 'sub_county')


# Location Management
@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'sub_counties_count', 'applications_count', 'created_at')
    search_fields = ('name', 'code')
    ordering = ('name',)
    
    def sub_counties_count(self, obj):
        return obj.sub_counties.count()
    sub_counties_count.short_description = 'Sub Counties'
    
    def applications_count(self, obj):
        return obj.current_applications.count()
    applications_count.short_description = 'Applications'


@admin.register(SubCounty)
class SubCountyAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'code', 'divisions_count', 'created_at')
    list_filter = ('county',)
    search_fields = ('name', 'code', 'county__name')
    ordering = ('county__name', 'name')
    
    def divisions_count(self, obj):
        return obj.divisions.count()
    divisions_count.short_description = 'Divisions'


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_county', 'county', 'locations_count')
    list_filter = ('sub_county__county',)
    search_fields = ('name', 'sub_county__name')
    
    def county(self, obj):
        return obj.sub_county.county.name
    county.short_description = 'County'
    
    def locations_count(self, obj):
        return obj.locations.count()
    locations_count.short_description = 'Locations'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'division', 'sub_county', 'county', 'sub_locations_count')
    list_filter = ('division__sub_county__county',)
    search_fields = ('name', 'division__name')
    
    def sub_county(self, obj):
        return obj.division.sub_county.name
    sub_county.short_description = 'Sub County'
    
    def county(self, obj):
        return obj.division.sub_county.county.name
    county.short_description = 'County'
    
    def sub_locations_count(self, obj):
        return obj.sub_locations.count()
    sub_locations_count.short_description = 'Sub Locations'


@admin.register(SubLocation)
class SubLocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'division', 'villages_count')
    search_fields = ('name', 'location__name')
    
    def division(self, obj):
        return obj.location.division.name
    division.short_description = 'Division'
    
    def villages_count(self, obj):
        return obj.villages.count()
    villages_count.short_description = 'Villages'


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('name', 'sub_location', 'location', 'full_address')
    search_fields = ('name', 'sub_location__name')
    
    def location(self, obj):
        return obj.sub_location.location.name
    location.short_description = 'Location'
    
    def full_address(self, obj):
        return f"{obj.name}, {obj.sub_location.location.division.sub_county.county.name}"
    full_address.short_description = 'Full Address'


# Administrative Offices
@admin.register(ChiefOffice)
class ChiefOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'sub_location', 'contact_phone', 'chiefs_count', 'is_active')
    list_filter = ('is_active', 'location__division__sub_county__county')
    search_fields = ('name', 'location__name', 'contact_phone')
    
    def chiefs_count(self, obj):
        return obj.chiefs.filter(is_active=True).count()
    chiefs_count.short_description = 'Active Chiefs'


@admin.register(Chief)
class ChiefAdmin(admin.ModelAdmin):
    list_display = ('user', 'office', 'employee_id', 'stamp_serial', 'appointment_date', 'applications_count', 'is_active')
    list_filter = ('is_active', 'appointment_date', 'office__location__division__sub_county__county')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id', 'stamp_serial')
    date_hierarchy = 'appointment_date'
    
    def applications_count(self, obj):
        return obj.idapplication_set.count()
    applications_count.short_description = 'Applications Handled'


@admin.register(ChiefStaff)
class ChiefStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'chief_office', 'position', 'reporting_chief', 'employee_id', 'is_active')
    list_filter = ('is_active', 'position', 'chief_office__location__division__sub_county__county')
    search_fields = ('user__username', 'employee_id', 'position')


@admin.register(DOOffice)
class DOOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'contact_phone', 'email', 'officers_count', 'applications_count', 'is_active')
    list_filter = ('is_active', 'county')
    search_fields = ('name', 'county__name', 'contact_phone', 'email')
    
    def officers_count(self, obj):
        return obj.officers.filter(is_active=True).count()
    officers_count.short_description = 'Active Officers'
    
    def applications_count(self, obj):
        return obj.idapplication_set.count()
    applications_count.short_description = 'Applications Processed'


@admin.register(DOOfficer)
class DOOfficerAdmin(admin.ModelAdmin):
    list_display = ('user', 'do_office', 'employee_id', 'appointment_date', 'applications_processed', 'is_active')
    list_filter = ('is_active', 'appointment_date', 'do_office__county')
    search_fields = ('user__username', 'employee_id')
    date_hierarchy = 'appointment_date'
    
    def applications_processed(self, obj):
        return obj.idapplication_set.count()
    applications_processed.short_description = 'Applications Processed'


@admin.register(DOStaff)
class DOStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'do_office', 'position', 'reporting_officer', 'employee_id', 'is_active')
    list_filter = ('is_active', 'position', 'do_office__county')
    search_fields = ('user__username', 'employee_id', 'position')


@admin.register(HudumaCentre)
class HudumaCentreAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'sub_county', 'contact_phone', 'staff_count', 'applications_count', 'is_active')
    list_filter = ('is_active', 'county')
    search_fields = ('name', 'county__name', 'contact_phone')
    
    def staff_count(self, obj):
        return obj.staff.filter(is_active=True).count()
    staff_count.short_description = 'Active Staff'
    
    def applications_count(self, obj):
        return obj.idapplication_set.count()
    applications_count.short_description = 'Applications'


@admin.register(HudumaStaff)
class HudumaStaffAdmin(admin.ModelAdmin):
    list_display = ('user', 'huduma_centre', 'position', 'employee_id', 'is_active')
    list_filter = ('is_active', 'position', 'huduma_centre__county')
    search_fields = ('user__username', 'employee_id', 'position')


# Birth Certificate Management
@admin.register(BirthCertificate)
class BirthCertificateAdmin(admin.ModelAdmin):
    list_display = ('certificate_number', 'full_name', 'date_of_birth', 'gender', 'county_of_birth', 'is_active', 'applications_count')
    list_filter = ('gender', 'is_active', 'is_verified', 'county_of_birth', 'registration_date')
    search_fields = ('certificate_number', 'serial_number', 'full_name', 'father_name', 'mother_name')
    date_hierarchy = 'date_of_birth'
    readonly_fields = ('serial_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Certificate Details', {
            'fields': ('certificate_number', 'serial_number', 'registration_date', 'issuing_office')
        }),
        ('Personal Information', {
            'fields': ('full_name', 'date_of_birth', 'place_of_birth', 'gender')
        }),
        ('Birth Location', {
            'fields': ('county_of_birth', 'sub_county_of_birth', 'division_of_birth', 'location_of_birth', 'sub_location_of_birth', 'village_of_birth')
        }),
        ('Family Information', {
            'fields': ('father_name', 'father_id', 'father_nationality', 'mother_name', 'mother_id', 'mother_nationality', 'guardian_name', 'guardian_id', 'guardian_relationship')
        }),
        ('Citizenship', {
            'fields': ('is_kenyan_born', 'naturalization_cert', 'citizenship_acquired_date')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
    )
    
    def applications_count(self, obj):
        return obj.idapplication_set.count()
    applications_count.short_description = 'ID Applications'


# Document Management
@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_required_for_new_id', 'is_required_for_replacement', 'is_required_for_name_change', 'max_file_size_mb')
    list_filter = ('is_required_for_new_id', 'is_required_for_replacement', 'is_required_for_name_change')
    search_fields = ('name', 'code', 'description')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'document_number', 'uploaded_by', 'is_verified', 'verified_by', 'file_size_mb', 'created_at')
    list_filter = ('document_type', 'is_verified', 'created_at')
    search_fields = ('document_number', 'uploaded_by__username', 'verified_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('file_size', 'created_at', 'updated_at')
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB" if obj.file_size else "0 MB"
    file_size_mb.short_description = 'File Size'


# ID Application Management
@admin.register(IDApplication)
class IDApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_number', 'full_name', 'application_type', 'status', 'entry_point', 'processing_days', 'created_at')
    list_filter = ('application_type', 'status', 'entry_point', 'created_at', 'current_county')
    search_fields = ('application_number', 'full_name', 'phone_number', 'birth_certificate__certificate_number')
    date_hierarchy = 'created_at'
    readonly_fields = ('application_id', 'application_number', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Application Details', {
            'fields': ('application_id', 'application_number', 'application_type', 'entry_point', 'status')
        }),
        ('Applicant Information', {
            'fields': ('applicant', 'birth_certificate', 'full_name', 'date_of_birth', 'place_of_birth', 'gender')
        }),
        ('Birth Location', {
            'fields': ('county_of_birth', 'sub_county_of_birth', 'division_of_birth', 'location_of_birth', 'sub_location_of_birth', 'village_of_birth')
        }),
        ('Current Address', {
            'fields': ('current_county', 'current_sub_county', 'current_division', 'current_location', 'current_sub_location', 'current_village')
        }),
        ('Family Information', {
            'fields': ('clan_name', 'father_name', 'father_id', 'mother_name', 'mother_id', 'guardian_name', 'guardian_id')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'alternative_phone', 'email', 'postal_address')
        }),
        ('Processing Information', {
            'fields': ('chief_office', 'chief', 'do_office', 'do_officer', 'huduma_centre')
        }),
        ('Replacement Details', {
            'fields': ('previous_id_number', 'police_ob_number', 'police_station', 'replacement_reason', 'replacement_fee', 'fee_paid'),
            'classes': ('collapse',)
        }),
        ('Name Change Details', {
            'fields': ('old_name', 'new_name', 'name_change_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def processing_days(self, obj):
        if obj.created_at:
            days = (timezone.now() - obj.created_at).days
            return f"{days} days"
        return "N/A"
    processing_days.short_description = 'Processing Time'
    
    actions = ['approve_applications', 'reject_applications', 'export_applications']
    
    def approve_applications(self, request, queryset):
        updated = queryset.filter(status='chief_review').update(status='chief_approved')
        self.message_user(request, f'{updated} applications approved.')
    approve_applications.short_description = "Approve selected applications"
    
    def reject_applications(self, request, queryset):
        updated = queryset.filter(status='chief_review').update(status='chief_rejected')
        self.message_user(request, f'{updated} applications rejected.')
    reject_applications.short_description = "Reject selected applications"


@admin.register(ApplicationDocument)
class ApplicationDocumentAdmin(admin.ModelAdmin):
    list_display = ('application', 'document_type', 'is_required', 'is_provided', 'is_verified', 'created_at')
    list_filter = ('document_type', 'is_required', 'is_provided', 'is_verified')
    search_fields = ('application__application_number', 'application__full_name')


# Chief Eligibility Letter
@admin.register(ChiefEligibilityLetter)
class ChiefEligibilityLetterAdmin(admin.ModelAdmin):
    list_display = ('letter_number', 'application', 'chief', 'full_name', 'is_eligible', 'is_valid_now', 'qr_code_preview', 'issued_at')
    list_filter = ('is_eligible', 'is_used', 'issued_at', 'chief__office__location__division__sub_county__county')
    search_fields = ('letter_number', 'application__application_number', 'full_name', 'verification_code')
    readonly_fields = ('verification_code', 'qr_code_preview', 'issued_at')
    date_hierarchy = 'issued_at'
    
    def is_valid_now(self, obj):
        return obj.is_valid()
    is_valid_now.boolean = True
    is_valid_now.short_description = 'Currently Valid'
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code.url)
        return "No QR Code"
    qr_code_preview.short_description = 'QR Code'


# Biometric Management
@admin.register(BiometricAppointment)
class BiometricAppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_reference', 'application', 'scheduled_date', 'scheduled_location', 'is_confirmed', 'is_completed', 'no_show')
    list_filter = ('is_confirmed', 'is_completed', 'no_show', 'scheduled_location', 'scheduled_date')
    search_fields = ('appointment_reference', 'application__application_number', 'application__full_name')
    date_hierarchy = 'scheduled_date'


@admin.register(BiometricData)
class BiometricDataAdmin(admin.ModelAdmin):
    list_display = ('application', 'captured_by', 'capture_location', 'is_verified', 'quality_scores', 'captured_at')
    list_filter = ('is_verified', 'capture_location', 'captured_at')
    search_fields = ('application__application_number', 'application__full_name')
    readonly_fields = ('captured_at',)
    
    def quality_scores(self, obj):
        return f"Photo: {obj.photo_quality_score}%, Fingerprint: {obj.fingerprint_quality_score}%, Signature: {obj.signature_quality_score}%"
    quality_scores.short_description = 'Quality Scores'


@admin.register(WaitingCard)
class WaitingCardAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'application', 'expected_collection_date', 'collection_location', 'is_active', 'qr_code_preview', 'issued_at')
    list_filter = ('is_active', 'is_collected', 'collection_location', 'expected_collection_date')
    search_fields = ('serial_number', 'application__application_number', 'application__full_name')
    readonly_fields = ('issued_at',)
    
    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="50" height="50" />', obj.qr_code.url)
        return "No QR Code"
    qr_code_preview.short_description = 'QR Code'


# National ID Management
@admin.register(NationalID)
class NationalIDAdmin(admin.ModelAdmin):
    list_display = ('id_number', 'full_name', 'date_of_birth', 'place_of_issue', 'is_active', 'is_collected', 'production_status', 'created_at')
    list_filter = ('is_active', 'is_printed', 'is_dispatched', 'is_ready_for_collection', 'is_collected', 'date_of_issue')
    search_fields = ('id_number', 'serial_number', 'full_name', 'application__application_number')
    readonly_fields = ('serial_number', 'created_at', 'updated_at')
    date_hierarchy = 'date_of_issue'
    
    def production_status(self, obj):
        if obj.is_collected:
            return format_html('<span style="color: green;">✓ Collected</span>')
        elif obj.is_ready_for_collection:
            return format_html('<span style="color: blue;">📋 Ready for Collection</span>')
        elif obj.is_dispatched:
            return format_html('<span style="color: orange;">🚚 Dispatched</span>')
        elif obj.is_printed:
            return format_html('<span style="color: purple;">🖨️ Printed</span>')
        else:
            return format_html('<span style="color: red;">⏳ Processing</span>')
    production_status.short_description = 'Production Status'


# Status History
@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('application', 'previous_status', 'new_status', 'changed_by', 'location_type', 'timestamp')
    list_filter = ('new_status', 'previous_status', 'location_type', 'timestamp')
    search_fields = ('application__application_number', 'application__full_name', 'changed_by__username')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'


# Notification Management
@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger_status', 'notification_type', 'is_active', 'created_at')
    list_filter = ('trigger_status', 'notification_type', 'is_active')
    search_fields = ('name', 'subject', 'message_template')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'recipient_contact', 'status', 'delivery_status', 'created_at')
    list_filter = ('notification_type', 'status', 'created_at')
    search_fields = ('recipient__username', 'recipient_contact', 'subject', 'application__application_number')
    readonly_fields = ('sent_at', 'delivered_at', 'read_at', 'created_at')
    
    def delivery_status(self, obj):
        if obj.status == 'delivered':
            return format_html('<span style="color: green;">✓ Delivered</span>')
        elif obj.status == 'sent':
            return format_html('<span style="color: blue;">📤 Sent</span>')
        elif obj.status == 'failed':
            return format_html('<span style="color: red;">❌ Failed</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    delivery_status.short_description = 'Delivery Status'


# Fee Management
@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('fee_type', 'amount', 'is_mandatory', 'is_active', 'effective_from', 'effective_to')
    list_filter = ('fee_type', 'is_mandatory', 'is_active', 'effective_from')
    search_fields = ('fee_type', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_reference', 'application', 'fee', 'amount', 'payment_method', 'status', 'paid_at')
    list_filter = ('payment_method', 'status', 'fee__fee_type', 'paid_at')
    search_fields = ('payment_reference', 'external_reference', 'application__application_number', 'payer_name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'paid_at'


# System Settings
@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value_preview', 'setting_type', 'category', 'is_public', 'updated_at')
    list_filter = ('setting_type', 'category', 'is_public')
    search_fields = ('key', 'description', 'value')
    readonly_fields = ('created_at', 'updated_at')
    
    def value_preview(self, obj):
        if len(obj.value) > 50:
            return f"{obj.value[:50]}..."
        return obj.value
    value_preview.short_description = 'Value'


# Audit and Security
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'content_type', 'object_repr', 'location_type', 'ip_address')
    list_filter = ('action', 'content_type', 'location_type', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'ip_address', 'notes')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be modified
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident_type', 'severity', 'affected_user', 'is_resolved', 'resolution_status', 'created_at')
    list_filter = ('incident_type', 'severity', 'is_resolved', 'created_at')
    search_fields = ('title', 'description', 'affected_user__username', 'ip_address')
    readonly_fields = ('created_at',)
    
    def resolution_status(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: green;">✓ Resolved</span>')
        else:
            return format_html('<span style="color: red;">❌ Open</span>')
    resolution_status.short_description = 'Status'


# Reports
@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'date_from', 'date_to', 'generated_by', 'file_link', 'generated_at')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('title', 'generated_by__username')
    readonly_fields = ('generated_at',)
    date_hierarchy = 'generated_at'
    
    def file_link(self, obj):
        if obj.file_path:
            return format_html('<a href="{}" target="_blank">Download Report</a>', obj.file_path.url)
        return "No File"
    file_link.short_description = 'Report File'


# Custom Admin Actions
def export_to_csv(modeladmin, request, queryset):
    """Export selected items to CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{modeladmin.model._meta.verbose_name_plural}.csv"'
    
    writer = csv.writer(response)
    # Write headers
    field_names = [field.name for field in modeladmin.model._meta.fields]
    writer.writerow(field_names)
    
    # Write data
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])
    
    return response

export_to_csv.short_description = "Export selected items to CSV"


# Add export action to all admin classes
admin_classes = [
    CustomUserAdmin, CountyAdmin, SubCountyAdmin, IDApplicationAdmin,
    BirthCertificateAdmin, ChiefEligibilityLetterAdmin, NationalIDAdmin
]

for admin_class in admin_classes:
    if hasattr(admin_class, 'actions'):
        admin_class.actions = list(admin_class.actions) + [export_to_csv]
    else:
        admin_class.actions = [export_to_csv]


# Dashboard customization
def admin_dashboard_stats(request):
    """Custom dashboard statistics"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'applications': {
            'total': IDApplication.objects.count(),
            'this_week': IDApplication.objects.filter(created_at__gte=week_ago).count(),
            'pending': IDApplication.objects.filter(
                status__in=['started', 'documents_uploaded', 'chief_review', 'do_review']
            ).count(),
            'approved': IDApplication.objects.filter(status='collected').count(),
        },
        'users': {
            'total': CustomUser.objects.count(),
            'citizens': CustomUser.objects.filter(user_type='mwananchi').count(),
            'officials': CustomUser.objects.exclude(user_type='mwananchi').count(),
            'verified': CustomUser.objects.filter(is_verified=True).count(),
        },
        'ids': {
            'produced': NationalID.objects.count(),
            'collected': NationalID.objects.filter(is_collected=True).count(),
            'ready_for_collection': NationalID.objects.filter(is_ready_for_collection=True, is_collected=False).count(),
        },
        'documents': {
            'uploaded': Document.objects.count(),
            'verified': Document.objects.filter(is_verified=True).count(),
            'pending_verification': Document.objects.filter(is_verified=False).count(),
        }
    }
    
    return stats


# Custom admin index template context
def admin_index_context(request):
    """Add custom context to admin index"""
    context = admin_dashboard_stats(request)
    
    # Recent applications
    context['recent_applications'] = IDApplication.objects.select_related(
        'applicant', 'county_of_birth'
    ).order_by('-created_at')[:10]
    
    # Processing time statistics
    from django.db.models import Avg, F
    context['avg_processing_time'] = IDApplication.objects.filter(
        status='collected'
    ).aggregate(
        avg_days=Avg(F('approved_at') - F('created_at'))
    )['avg_days']
    
    # County statistics
    context['county_stats'] = County.objects.annotate(
        application_count=Count('current_applications'),
        birth_count=Count('birth_certificates')
    ).order_by('-application_count')[:10]
    
    return context


# Custom filters
class StatusFilter(admin.SimpleListFilter):
    """Custom filter for application status grouping"""
    title = 'Status Category'
    parameter_name = 'status_category'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('processing', 'In Processing'),
            ('completed', 'Completed'),
            ('rejected', 'Rejected'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(status__in=['started', 'documents_uploaded', 'chief_review', 'do_review'])
        elif self.value() == 'approved':
            return queryset.filter(status__in=['chief_approved', 'do_approved'])
        elif self.value() == 'processing':
            return queryset.filter(status__in=['biometrics_scheduled', 'biometrics_taken', 'processing'])
        elif self.value() == 'completed':
            return queryset.filter(status__in=['ready_for_collection', 'collected'])
        elif self.value() == 'rejected':
            return queryset.filter(status__in=['chief_rejected', 'do_rejected', 'rejected'])


class DateRangeFilter(admin.SimpleListFilter):
    """Custom date range filter"""
    title = 'Application Date Range'
    parameter_name = 'date_range'

    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
            ('year', 'This Year'),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'today':
            return queryset.filter(created_at__date=now.date())
        elif self.value() == 'week':
            week_start = now - timedelta(days=now.weekday())
            return queryset.filter(created_at__gte=week_start)
        elif self.value() == 'month':
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=month_start)
        elif self.value() == 'quarter':
            quarter_start = now.replace(month=((now.month-1)//3)*3+1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=quarter_start)
        elif self.value() == 'year':
            year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return queryset.filter(created_at__gte=year_start)


# Add custom filters to IDApplicationAdmin
IDApplicationAdmin.list_filter = IDApplicationAdmin.list_filter + (StatusFilter, DateRangeFilter)


# Inline Admin Classes
class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0
    readonly_fields = ('is_verified', 'created_at')
    fields = ('document_type', 'document', 'is_required', 'is_provided', 'is_verified', 'notes')


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ('timestamp', 'previous_status', 'new_status', 'changed_by')
    fields = ('timestamp', 'previous_status', 'new_status', 'changed_by', 'change_reason', 'notes')
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request, obj=None):
        return False


class NotificationInline(admin.TabularInline):
    model = Notification
    extra = 0
    readonly_fields = ('created_at', 'sent_at', 'status')
    fields = ('notification_type', 'recipient_contact', 'subject', 'status', 'sent_at')
    
    def has_add_permission(self, request, obj=None):
        return False


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_reference', 'paid_at', 'created_at')
    fields = ('fee', 'amount', 'payment_method', 'payment_reference', 'status', 'paid_at')


# Add inlines to IDApplicationAdmin
IDApplicationAdmin.inlines = [
    ApplicationDocumentInline,
    ApplicationStatusHistoryInline,
    NotificationInline,
    PaymentInline
]


# Custom admin widgets and forms
from django import forms
from django.contrib.admin.widgets import AdminFileWidget

class ImagePreviewWidget(AdminFileWidget):
    """Widget to show image preview in admin"""
    def render(self, name, value, attrs=None, renderer=None):
        output = super().render(name, value, attrs, renderer)
        if value and getattr(value, 'url', None):
            output += format_html(
                '<div style="margin-top: 10px;"><img src="{}" style="max-width: 200px; max-height: 200px;" /></div>',
                value.url
            )
        return mark_safe(output)


class QRCodePreviewWidget(forms.widgets.Widget):
    """Widget to show QR code preview"""
    def render(self, name, value, attrs=None, renderer=None):
        if value:
            return format_html(
                '<div><img src="{}" style="width: 100px; height: 100px;" /><br><small>QR Code</small></div>',
                value.url
            )
        return '<div><small>No QR Code generated yet</small></div>'


# Custom forms for specific models
class BirthCertificateForm(forms.ModelForm):
    class Meta:
        model = BirthCertificate
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'registration_date': forms.DateInput(attrs={'type': 'date'}),
            'citizenship_acquired_date': forms.DateInput(attrs={'type': 'date'}),
        }


class IDApplicationForm(forms.ModelForm):
    class Meta:
        model = IDApplication
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }


class BiometricDataForm(forms.ModelForm):
    class Meta:
        model = BiometricData
        fields = '__all__'
        widgets = {
            'passport_photo': ImagePreviewWidget,
            'signature': ImagePreviewWidget,
        }


class ChiefEligibilityLetterForm(forms.ModelForm):
    class Meta:
        model = ChiefEligibilityLetter
        fields = '__all__'
        widgets = {
            'qr_code': QRCodePreviewWidget,
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class WaitingCardForm(forms.ModelForm):
    class Meta:
        model = WaitingCard
        fields = '__all__'
        widgets = {
            'qr_code': QRCodePreviewWidget,
            'expected_collection_date': forms.DateInput(attrs={'type': 'date'}),
        }


# Apply custom forms to admin classes
BirthCertificateAdmin.form = BirthCertificateForm
IDApplicationAdmin.form = IDApplicationForm
BiometricDataAdmin.form = BiometricDataForm
ChiefEligibilityLetterAdmin.form = ChiefEligibilityLetterForm
WaitingCardAdmin.form = WaitingCardForm


# Management commands integration
class ManagementCommandAdmin(admin.ModelAdmin):
    """Admin interface for running management commands"""
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['management_commands'] = [
            {'name': 'Generate Daily Report', 'command': 'generate_daily_report'},
            {'name': 'Send Pending Notifications', 'command': 'send_notifications'},
            {'name': 'Update Application Status', 'command': 'update_statuses'},
            {'name': 'Backup Database', 'command': 'backup_db'},
            {'name': 'Generate ID Numbers', 'command': 'generate_id_numbers'},
        ]
        return super().changelist_view(request, extra_context)


# Advanced search functionality
class AdvancedSearchForm(forms.Form):
    search_term = forms.CharField(max_length=200, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    status = forms.ChoiceField(
        choices=[('', 'All')] + list(IDApplication.APPLICATION_STATUS),
        required=False
    )
    county = forms.ModelChoiceField(queryset=County.objects.all(), required=False)


# Bulk operations
class BulkOperationsAdmin:
    """Mixin for bulk operations"""
    
    def bulk_approve(self, request, queryset):
        """Bulk approve applications"""
        count = 0
        for obj in queryset:
            if obj.status in ['chief_review', 'do_review']:
                if obj.status == 'chief_review':
                    obj.status = 'chief_approved'
                elif obj.status == 'do_review':
                    obj.status = 'do_approved'
                obj.save()
                count += 1
        
        self.message_user(request, f'{count} applications approved successfully.')
    
    bulk_approve.short_description = "Bulk approve selected applications"
    
    def bulk_reject(self, request, queryset):
        """Bulk reject applications"""
        count = 0
        for obj in queryset:
            if obj.status in ['chief_review', 'do_review']:
                if obj.status == 'chief_review':
                    obj.status = 'chief_rejected'
                elif obj.status == 'do_review':
                    obj.status = 'do_rejected'
                obj.save()
                count += 1
        
        self.message_user(request, f'{count} applications rejected successfully.')
    
    bulk_reject.short_description = "Bulk reject selected applications"
    
    def generate_reports(self, request, queryset):
        """Generate reports for selected items"""
        # Implementation for report generation
        self.message_user(request, f'Report generation started for {queryset.count()} items.')
    
    generate_reports.short_description = "Generate reports for selected items"


# Apply bulk operations to relevant admin classes
class EnhancedIDApplicationAdmin(IDApplicationAdmin, BulkOperationsAdmin):
    actions = IDApplicationAdmin.actions + ['bulk_approve', 'bulk_reject', 'generate_reports']


# Replace the original admin registration
admin.site.unregister(IDApplication)
admin.site.register(IDApplication, EnhancedIDApplicationAdmin)


# Custom admin site configuration
admin.site.site_header = "Kenyan National ID Management System"
admin.site.site_title = "Kenyan ID Admin"
admin.site.index_title = "System Administration Dashboard"

# Add custom CSS and JavaScript
class KenyanIDAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        # Add dashboard statistics
        context.update(admin_index_context(request))
        return context

# Replace default admin site
admin_site = KenyanIDAdminSite(name='kenyan_id_admin')

# Re-register all models with the custom admin site
for model, admin_class in admin.site._registry.items():
    admin_site.register(model, admin_class.__class__)


# Additional utility functions for admin
def generate_qr_code_for_admin(data, size=(200, 200)):
    """Generate QR code for admin display"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    return base64.b64encode(buffer.getvalue()).decode()


def format_processing_time(start_date, end_date=None):
    """Format processing time for admin display"""
    if not start_date:
        return "N/A"
    
    end = end_date or timezone.now()
    delta = end - start_date
    
    if delta.days == 0:
        return f"{delta.seconds // 3600} hours"
    elif delta.days == 1:
        return "1 day"
    else:
        return f"{delta.days} days"


# Performance optimizations for admin
def optimize_queryset(queryset, select_related_fields=None, prefetch_related_fields=None):
    """Optimize queryset for admin views"""
    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)
    
    if prefetch_related_fields:
        queryset = queryset.prefetch_related(*prefetch_related_fields)
    
    return queryset


# Apply optimizations to frequently accessed admin classes
CustomUserAdmin.get_queryset = lambda self, request: optimize_queryset(
    super(CustomUserAdmin, self).get_queryset(request),
    select_related_fields=['county', 'sub_county']
)

IDApplicationAdmin.get_queryset = lambda self, request: optimize_queryset(
    super(IDApplicationAdmin, self).get_queryset(request),
    select_related_fields=[
        'applicant', 'birth_certificate', 'current_county', 'chief', 'do_office'
    ],
    prefetch_related_fields=['application_documents', 'status_history']
)