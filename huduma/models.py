# models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal
import uuid
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
import random
import string


# Location Models
class County(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Counties"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SubCounty(models.Model):
    name = models.CharField(max_length=100)
    county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='sub_counties')
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['county', 'code']
        verbose_name_plural = "Sub Counties"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.county.name}"


class Division(models.Model):
    name = models.CharField(max_length=100)
    sub_county = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='divisions')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.sub_county.name}"


class Location(models.Model):
    name = models.CharField(max_length=100)
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='locations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.division.name}"


class SubLocation(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='sub_locations')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.location.name}"


class Village(models.Model):
    name = models.CharField(max_length=100)
    sub_location = models.ForeignKey(SubLocation, on_delete=models.CASCADE, related_name='villages')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.sub_location.name}"


# User Management
class CustomUser(AbstractUser):
    USER_TYPES = (
        ('mwananchi', 'Mwananchi (Citizen)'),
        ('chief_staff', 'Chief Staff'),
        ('chief', 'Chief'),
        ('do_staff', 'DO Staff'),
        ('do_officer', 'DO Officer'),
        ('huduma_staff', 'Huduma Staff'),
        ('admin', 'System Admin'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='mwananchi')
    phone_number = models.CharField(
        max_length=15, 
        validators=[RegexValidator(r'^\+?254[0-9]{9}$', 'Enter a valid Kenyan phone number')],
        null=True, 
        blank=True
    )
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    national_id = models.CharField(max_length=20, null=True, blank=True, unique=True)
    is_verified = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Location details
    county = models.ForeignKey(County, on_delete=models.SET_NULL, null=True, blank=True)
    sub_county = models.ForeignKey(SubCounty, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"


# Administrative Offices
class ChiefOffice(models.Model):
    name = models.CharField(max_length=200)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    sub_location = models.ForeignKey(SubLocation, on_delete=models.CASCADE)
    address = models.TextField()
    contact_phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chief Office - {self.name}"


class Chief(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    office = models.ForeignKey(ChiefOffice, on_delete=models.CASCADE, related_name='chiefs')
    employee_id = models.CharField(max_length=50, unique=True)
    stamp_serial = models.CharField(max_length=50, unique=True)
    appointment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chief {self.user.get_full_name()} - {self.office.name}"


class ChiefStaff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    chief_office = models.ForeignKey(ChiefOffice, on_delete=models.CASCADE, related_name='staff')
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    reporting_chief = models.ForeignKey(Chief, on_delete=models.CASCADE, related_name='staff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Chief Staff {self.user.get_full_name()} - {self.position}"


class DOOffice(models.Model):
    name = models.CharField(max_length=200)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    address = models.TextField()
    contact_phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    postal_address = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"DO Office - {self.name}"


class DOOfficer(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    do_office = models.ForeignKey(DOOffice, on_delete=models.CASCADE, related_name='officers')
    employee_id = models.CharField(max_length=50, unique=True)
    appointment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"DO Officer {self.user.get_full_name()}"


class DOStaff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    do_office = models.ForeignKey(DOOffice, on_delete=models.CASCADE, related_name='staff')
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    reporting_officer = models.ForeignKey(DOOfficer, on_delete=models.CASCADE, related_name='staff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"DO Staff {self.user.get_full_name()} - {self.position}"


class HudumaCentre(models.Model):
    name = models.CharField(max_length=200)
    county = models.ForeignKey(County, on_delete=models.CASCADE)
    sub_county = models.ForeignKey(SubCounty, on_delete=models.CASCADE)
    address = models.TextField()
    contact_phone = models.CharField(max_length=15)
    email = models.EmailField(null=True, blank=True)
    services_offered = models.TextField()
    operating_hours = models.CharField(max_length=100, default="Monday-Friday 8:00AM-5:00PM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Huduma Centre - {self.name}"


class HudumaStaff(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    huduma_centre = models.ForeignKey(HudumaCentre, on_delete=models.CASCADE, related_name='staff')
    position = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Huduma Staff {self.user.get_full_name()} - {self.position}"


# Birth Certificate Master Database
class BirthCertificate(models.Model):
    """Master database of all Kenyan birth certificates"""
    certificate_number = models.CharField(max_length=50, unique=True, primary_key=True)
    serial_number = models.CharField(max_length=50, unique=True)
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    
    # Birth Location
    county_of_birth = models.ForeignKey(County, on_delete=models.CASCADE, related_name='birth_certificates')
    sub_county_of_birth = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='birth_certificates')
    division_of_birth = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='birth_certificates')
    location_of_birth = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='birth_certificates')
    sub_location_of_birth = models.ForeignKey(SubLocation, on_delete=models.CASCADE, related_name='birth_certificates')
    village_of_birth = models.ForeignKey(Village, on_delete=models.CASCADE, related_name='birth_certificates')
    
    # Family Information
    father_name = models.CharField(max_length=200, null=True, blank=True)
    father_id = models.CharField(max_length=20, null=True, blank=True)
    father_nationality = models.CharField(max_length=50, default='KENYAN')
    
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    mother_id = models.CharField(max_length=20, null=True, blank=True)
    mother_nationality = models.CharField(max_length=50, default='KENYAN')
    
    guardian_name = models.CharField(max_length=200, null=True, blank=True)
    guardian_id = models.CharField(max_length=20, null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    
    # Registration Details
    registration_date = models.DateField()
    issuing_office = models.CharField(max_length=200)
    registrar_name = models.CharField(max_length=200)
    
    # For non-Kenyan born citizens
    is_kenyan_born = models.BooleanField(default=True)
    naturalization_cert = models.CharField(max_length=100, null=True, blank=True)
    citizenship_acquired_date = models.DateField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.serial_number:
            self.serial_number = self.generate_serial_number()
        super().save(*args, **kwargs)
    
    def generate_serial_number(self):
        """Generate unique birth certificate serial number"""
        while True:
            serial = f"BC{random.randint(100000, 999999)}{self.date_of_birth.year}"
            if not BirthCertificate.objects.filter(serial_number=serial).exists():
                return serial
    
    def __str__(self):
        return f"{self.full_name} - {self.certificate_number}"


# Document Management
class DocumentType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    is_required_for_new_id = models.BooleanField(default=False)
    is_required_for_replacement = models.BooleanField(default=False)
    is_required_for_name_change = models.BooleanField(default=False)
    max_file_size_mb = models.IntegerField(default=5)  # Maximum file size in MB
    allowed_formats = models.CharField(max_length=100, default="pdf,jpg,jpeg,png")
    
    def __str__(self):
        return self.name


class Document(models.Model):
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    document_number = models.CharField(max_length=100, null=True, blank=True)
    
    # File storage
    file_original = models.FileField(upload_to='documents/original/')
    file_copy = models.FileField(upload_to='documents/copies/', null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_documents')
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(null=True, blank=True)
    
    # Upload details
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='uploaded_documents')
    file_size = models.IntegerField(default=0)  # File size in bytes
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.document_type.name} - {self.document_number or 'No Number'}"


# ID Application Process
class IDApplication(models.Model):
    APPLICATION_STATUS = (
        ('started', 'Application Started'),
        ('documents_uploaded', 'Documents Uploaded'),
        ('chief_review', 'Under Chief Review'),
        ('chief_approved', 'Chief Approved'),
        ('chief_rejected', 'Chief Rejected'),
        ('do_review', 'Under DO Review'),
        ('do_approved', 'DO Approved'),
        ('do_rejected', 'DO Rejected'),
        ('biometrics_scheduled', 'Biometrics Scheduled'),
        ('biometrics_taken', 'Biometrics Captured'),
        ('processing', 'ID Processing'),
        ('ready_for_collection', 'Ready for Collection'),
        ('collected', 'ID Collected'),
        ('rejected', 'Application Rejected'),
        ('cancelled', 'Application Cancelled'),
    )
    
    APPLICATION_TYPES = (
        ('new', 'New ID Application'),
        ('replacement', 'ID Replacement'),
        ('name_change', 'Name Change'),
    )
    
    ENTRY_POINTS = (
        ('chief', 'Started from Chief Office'),
        ('huduma', 'Started from Huduma Centre'),
        ('online', 'Started Online'),
    )
    
    REPLACEMENT_REASONS = (
        ('lost', 'Lost'),
        ('stolen', 'Stolen'),
        ('damaged', 'Damaged'),
        ('mutilated', 'Mutilated'),
    )
    
    # Basic Application Info
    application_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    application_number = models.CharField(max_length=50, unique=True)
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES, default='new')
    entry_point = models.CharField(max_length=20, choices=ENTRY_POINTS)
    status = models.CharField(max_length=30, choices=APPLICATION_STATUS, default='started')
    
    # Applicant Information
    applicant = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='id_applications')
    birth_certificate = models.ForeignKey(BirthCertificate, on_delete=models.CASCADE)
    
    # Personal Details (copied from birth certificate but can be updated)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    
    # Birth Location
    county_of_birth = models.ForeignKey(County, on_delete=models.CASCADE, related_name='birth_applications')
    sub_county_of_birth = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='birth_applications')
    division_of_birth = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='birth_applications')
    location_of_birth = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='birth_applications')
    sub_location_of_birth = models.ForeignKey(SubLocation, on_delete=models.CASCADE, related_name='birth_applications')
    village_of_birth = models.ForeignKey(Village, on_delete=models.CASCADE, related_name='birth_applications')
    
    # Current Address
    current_county = models.ForeignKey(County, on_delete=models.CASCADE, related_name='current_applications')
    current_sub_county = models.ForeignKey(SubCounty, on_delete=models.CASCADE, related_name='current_applications')
    current_division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name='current_applications')
    current_location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='current_applications')
    current_sub_location = models.ForeignKey(SubLocation, on_delete=models.CASCADE, related_name='current_applications')
    current_village = models.ForeignKey(Village, on_delete=models.CASCADE, related_name='current_applications')
    
    # Family Information
    clan_name = models.CharField(max_length=100, null=True, blank=True)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    father_id = models.CharField(max_length=20, null=True, blank=True)
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    mother_id = models.CharField(max_length=20, null=True, blank=True)
    guardian_name = models.CharField(max_length=200, null=True, blank=True)
    guardian_id = models.CharField(max_length=20, null=True, blank=True)
    guardian_relationship = models.CharField(max_length=50, null=True, blank=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=15)
    alternative_phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    postal_address = models.CharField(max_length=200, null=True, blank=True)
    
    # Processing Information
    chief_office = models.ForeignKey(ChiefOffice, on_delete=models.SET_NULL, null=True, blank=True)
    chief = models.ForeignKey(Chief, on_delete=models.SET_NULL, null=True, blank=True)
    do_office = models.ForeignKey(DOOffice, on_delete=models.SET_NULL, null=True, blank=True)
    do_officer = models.ForeignKey(DOOfficer, on_delete=models.SET_NULL, null=True, blank=True)
    huduma_centre = models.ForeignKey(HudumaCentre, on_delete=models.SET_NULL, null=True, blank=True)
    
    # For replacements
    previous_id_number = models.CharField(max_length=20, null=True, blank=True)
    police_ob_number = models.CharField(max_length=50, null=True, blank=True)
    police_station = models.CharField(max_length=100, null=True, blank=True)
    replacement_reason = models.CharField(max_length=20, choices=REPLACEMENT_REASONS, null=True, blank=True)
    replacement_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1000.00'))
    fee_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)
    
    # For name changes
    old_name = models.CharField(max_length=200, null=True, blank=True)
    new_name = models.CharField(max_length=200, null=True, blank=True)
    name_change_reason = models.TextField(null=True, blank=True)
    
    # Application dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.application_number:
            self.application_number = self.generate_application_number()
        
        if not self.submitted_at and self.status not in ['started', 'documents_uploaded']:
            self.submitted_at = timezone.now()
        
        if not self.approved_at and self.status in ['do_approved', 'biometrics_scheduled']:
            self.approved_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def generate_application_number(self):
        """Generate unique application number"""
        year = timezone.now().year
        while True:
            number = f"ID{year}{random.randint(100000, 999999)}"
            if not IDApplication.objects.filter(application_number=number).exists():
                return number
    
    def __str__(self):
        return f"ID Application - {self.full_name} ({self.application_number})"


class ApplicationDocument(models.Model):
    """Through model for Application-Document relationship"""
    application = models.ForeignKey(IDApplication, on_delete=models.CASCADE, related_name='application_documents')
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=True)
    is_provided = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['application', 'document_type']
    
    def __str__(self):
        return f"{self.application.application_number} - {self.document_type.name}"


# Chief's Eligibility Letter
class ChiefEligibilityLetter(models.Model):
    application = models.OneToOneField(IDApplication, on_delete=models.CASCADE, related_name='chief_letter')
    chief = models.ForeignKey(Chief, on_delete=models.CASCADE)
    letter_number = models.CharField(max_length=50, unique=True)
    
    # Letter content
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    father_name = models.CharField(max_length=200, null=True, blank=True)
    mother_name = models.CharField(max_length=200, null=True, blank=True)
    
    # Eligibility determination
    is_eligible = models.BooleanField(default=True)
    eligibility_reason = models.TextField()
    additional_notes = models.TextField(null=True, blank=True)
    
    # Digital verification
    qr_code = models.ImageField(upload_to='chief_letters/qr_codes/', null=True, blank=True)
    verification_code = models.CharField(max_length=100, unique=True)
    digital_signature = models.TextField(null=True, blank=True)  # Can store encrypted signature
    
    # Validity
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # Letter validity period (usually 30 days)
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.letter_number:
            self.letter_number = self.generate_letter_number()
        
        if not self.verification_code:
            self.verification_code = str(uuid.uuid4())
        
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=30)
        
        # Generate QR Code
        if not self.qr_code:
            qr_data = {
                'type': 'CHIEF_ELIGIBILITY_LETTER',
                'letter_number': self.letter_number,
                'verification_code': self.verification_code,
                'application_id': str(self.application.application_id),
                'chief_stamp': self.chief.stamp_serial,
                'issued_date': self.issued_at.strftime('%Y-%m-%d') if self.issued_at else timezone.now().strftime('%Y-%m-%d')
            }
            
            qr_string = f"{qr_data['type']}|{qr_data['letter_number']}|{qr_data['verification_code']}|{qr_data['application_id']}|{qr_data['chief_stamp']}|{qr_data['issued_date']}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_io = BytesIO()
            qr_image.save(qr_io, 'PNG')
            qr_file = File(qr_io, name=f'chief_letter_{self.letter_number}.png')
            self.qr_code.save(f'chief_letter_{self.letter_number}.png', qr_file, save=False)
        
        super().save(*args, **kwargs)
    
    def generate_letter_number(self):
        """Generate unique letter number"""
        chief_code = self.chief.office.location.name[:3].upper()
        year = timezone.now().year
        while True:
            number = f"EL/{chief_code}/{year}/{random.randint(1000, 9999)}"
            if not ChiefEligibilityLetter.objects.filter(letter_number=number).exists():
                return number
    
    def is_valid(self):
        """Check if letter is still valid"""
        return timezone.now() <= self.expires_at and not self.is_used
    
    def __str__(self):
        return f"Chief Letter - {self.letter_number} for {self.full_name}"


# Biometric Data Capture
class BiometricAppointment(models.Model):
    application = models.OneToOneField(IDApplication, on_delete=models.CASCADE, related_name='biometric_appointment')
    scheduled_date = models.DateTimeField()
    scheduled_location = models.ForeignKey(DOOffice, on_delete=models.CASCADE)
    appointment_reference = models.CharField(max_length=50, unique=True)
    
    # Status
    is_confirmed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    no_show = models.BooleanField(default=False)
    
    # Rescheduling
    reschedule_count = models.IntegerField(default=0)
    max_reschedules = models.IntegerField(default=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.appointment_reference:
            self.appointment_reference = f"BIO{random.randint(100000, 999999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Biometric Appointment - {self.appointment_reference} for {self.application.full_name}"


class BiometricData(models.Model):
    """Biometric data captured during ID processing"""
    application = models.OneToOneField(IDApplication, on_delete=models.CASCADE, related_name='biometric_data')
    
    # Fingerprints (stored as encoded data or file paths)
    right_thumb = models.TextField(null=True, blank=True)  # Base64 encoded fingerprint data
    left_thumb = models.TextField(null=True, blank=True)
    right_index = models.TextField(null=True, blank=True)
    left_index = models.TextField(null=True, blank=True)
    right_middle = models.TextField(null=True, blank=True)
    left_middle = models.TextField(null=True, blank=True)
    
    # Biometric images
    fingerprint_card = models.ImageField(upload_to='biometrics/fingerprints/', null=True, blank=True)
    
    # Passport photo
    passport_photo = models.ImageField(upload_to='biometrics/photos/')
    
    # Signature
    signature = models.ImageField(upload_to='biometrics/signatures/', null=True, blank=True)
    
    # Quality scores (0-100)
    photo_quality_score = models.IntegerField(default=0)
    fingerprint_quality_score = models.IntegerField(default=0)
    signature_quality_score = models.IntegerField(default=0)
    
    # Capture details
    captured_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='captured_biometrics')
    capture_device = models.CharField(max_length=100, null=True, blank=True)
    capture_location = models.ForeignKey(DOOffice, on_delete=models.CASCADE)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_biometrics')
    verification_notes = models.TextField(null=True, blank=True)
    
    captured_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Biometrics - {self.application.full_name} ({self.application.application_number})"


# Waiting Card
class WaitingCard(models.Model):
    """Waiting card issued after biometric capture"""
    application = models.OneToOneField(IDApplication, on_delete=models.CASCADE, related_name='waiting_card')
    serial_number = models.CharField(max_length=50, unique=True)
    
    # Collection details
    expected_collection_date = models.DateField()
    collection_location = models.ForeignKey(DOOffice, on_delete=models.CASCADE)
    collection_instructions = models.TextField()
    
    # QR Code for tracking
    qr_code = models.ImageField(upload_to='waiting_cards/qr_codes/', null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_collected = models.BooleanField(default=False)
    
    issued_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.serial_number:
            self.serial_number = self.generate_serial_number()
        
        # Generate QR Code for waiting card
        if not self.qr_code:
            qr_data = f"WAITING_CARD|{self.serial_number}|{self.application.application_id}|{self.expected_collection_date.strftime('%Y-%m-%d')}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_io = BytesIO()
            qr_image.save(qr_io, 'PNG')
            qr_file = File(qr_io, name=f'waiting_card_{self.serial_number}.png')
            self.qr_code.save(f'waiting_card_{self.serial_number}.png', qr_file, save=False)
        
        super().save(*args, **kwargs)
    
    def generate_serial_number(self):
        """Generate unique waiting card serial number"""
        while True:
            serial = f"WC{random.randint(100000, 999999)}{timezone.now().year}"
            if not WaitingCard.objects.filter(serial_number=serial).exists():
                return serial
    
    def __str__(self):
        return f"Waiting Card - {self.serial_number} for {self.application.full_name}"


# National ID
class NationalID(models.Model):
    """The actual National ID record"""
    application = models.OneToOneField(IDApplication, on_delete=models.CASCADE, related_name='national_id')
    id_number = models.CharField(max_length=20, unique=True)
    
    # Personal Information (from application)
    full_name = models.CharField(max_length=200)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    
    # Address information
    district_of_birth = models.CharField(max_length=100)  # Legacy field
    division_of_birth = models.CharField(max_length=100)
    location_of_birth = models.CharField(max_length=100)
    sub_location = models.CharField(max_length=100)
    
    # Family
    clan = models.CharField(max_length=100, null=True, blank=True)
    
    # ID Details
    place_of_issue = models.CharField(max_length=200)
    date_of_issue = models.DateField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)  # Some IDs don't expire
    
    # Physical ID
    serial_number = models.CharField(max_length=50, unique=True)
    security_features = models.JSONField(default=dict)  # Store security feature data
    
    # Status
    is_active = models.BooleanField(default=True)
    is_printed = models.BooleanField(default=False)
    is_dispatched = models.BooleanField(default=False)
    is_ready_for_collection = models.BooleanField(default=False)
    is_collected = models.BooleanField(default=False)
    
    # Collection details
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_ids')
    collection_location = models.ForeignKey(DOOffice, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Photo and Signature (copied from biometric data)
    photo = models.ImageField(upload_to='id_photos/')
    signature = models.ImageField(upload_to='id_signatures/', null=True, blank=True)
    
    # Production tracking
    printed_at = models.DateTimeField(null=True, blank=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.id_number:
            self.id_number = self.generate_id_number()
        
        if not self.serial_number:
            self.serial_number = self.generate_serial_number()
        
        super().save(*args, **kwargs)
    
    def generate_id_number(self):
        """Generate unique National ID number"""
        while True:
            # Kenyan ID format: 8 digits
            id_num = f"{random.randint(10000000, 99999999)}"
            if not NationalID.objects.filter(id_number=id_num).exists():
                return id_num
    
    def generate_serial_number(self):
        """Generate unique ID serial number"""
        year = timezone.now().year
        while True:
            serial = f"ID{year}{random.randint(100000, 999999)}"
            if not NationalID.objects.filter(serial_number=serial).exists():
                return serial
    
    def __str__(self):
        return f"National ID - {self.id_number} ({self.full_name})"


# Status Tracking
class ApplicationStatusHistory(models.Model):
    """Track all status changes for an application"""
    application = models.ForeignKey(IDApplication, on_delete=models.CASCADE, related_name='status_history')
    previous_status = models.CharField(max_length=30, null=True, blank=True)
    new_status = models.CharField(max_length=30, choices=IDApplication.APPLICATION_STATUS)
    changed_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    change_reason = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Location where change occurred
    location_type = models.CharField(max_length=20, choices=[
        ('chief_office', 'Chief Office'),
        ('do_office', 'DO Office'),
        ('huduma_centre', 'Huduma Centre'),
        ('online', 'Online System')
    ], null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Application Status Histories"
    
    def __str__(self):
        return f"{self.application.application_number} - {self.get_new_status_display()} at {self.timestamp}"


# Notification System
class NotificationTemplate(models.Model):
    """Templates for different types of notifications"""
    name = models.CharField(max_length=100, unique=True)
    subject = models.CharField(max_length=200)
    message_template = models.TextField()
    notification_type = models.CharField(max_length=20, choices=[
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('both', 'SMS and Email')
    ])
    trigger_status = models.CharField(max_length=30, choices=IDApplication.APPLICATION_STATUS)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_trigger_status_display()}"


class Notification(models.Model):
    """SMS/Email notifications for applicants"""
    NOTIFICATION_TYPES = (
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('system', 'System Notification'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    )
    
    application = models.ForeignKey(IDApplication, on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE, null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    recipient_contact = models.CharField(max_length=100)  # Phone or email
    subject = models.CharField(max_length=200, null=True, blank=True)
    message = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    
    # Delivery tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_notification_type_display()} to {self.recipient_contact}"


# Fee Management
class Fee(models.Model):
    """Fee structure for different services"""
    FEE_TYPES = (
        ('new_id', 'New ID Application'),
        ('replacement', 'ID Replacement'),
        ('name_change', 'Name Change'),
        ('duplicate_certificate', 'Duplicate Certificate'),
        ('urgent_processing', 'Urgent Processing'),
    )
    
    fee_type = models.CharField(max_length=30, choices=FEE_TYPES, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Effective dates
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_fee_type_display()} - KES {self.amount}"


class Payment(models.Model):
    """Payment records"""
    PAYMENT_METHODS = (
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('card', 'Card Payment'),
    )
    
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    application = models.ForeignKey(IDApplication, on_delete=models.CASCADE, related_name='payments')
    fee = models.ForeignKey(Fee, on_delete=models.CASCADE)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=100, null=True, blank=True)  # M-Pesa code, etc.
    
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Payment details
    payer_phone = models.CharField(max_length=15, null=True, blank=True)
    payer_name = models.CharField(max_length=200, null=True, blank=True)
    
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            self.payment_reference = f"PAY{random.randint(1000000, 9999999)}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment {self.payment_reference} - KES {self.amount}"


# System Configuration
class SystemSettings(models.Model):
    """System-wide settings and configurations"""
    SETTING_TYPES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    )
    
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    setting_type = models.CharField(max_length=20, choices=SETTING_TYPES, default='text')
    description = models.TextField()
    category = models.CharField(max_length=50, default='general')
    
    is_public = models.BooleanField(default=False)  # Whether setting can be viewed by non-admins
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.key} = {self.value}"


# Audit and Security
class AuditLog(models.Model):
    """Comprehensive audit trail for all system activities"""
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('verify', 'Verify'),
        ('collect', 'Collect'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Object being acted upon
    content_type = models.CharField(max_length=100)  # Model name
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)  # String representation of object
    
    # Change details
    changes = models.JSONField(null=True, blank=True)  # Store what changed
    notes = models.TextField(null=True, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)
    
    # Location
    location_type = models.CharField(max_length=20, choices=[
        ('chief_office', 'Chief Office'),
        ('do_office', 'DO Office'),
        ('huduma_centre', 'Huduma Centre'),
        ('online', 'Online'),
    ], null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} {self.action} {self.content_type} at {self.timestamp}"


class SecurityIncident(models.Model):
    """Track security incidents and suspicious activities"""
    INCIDENT_TYPES = (
        ('unauthorized_access', 'Unauthorized Access Attempt'),
        ('multiple_failures', 'Multiple Login Failures'),
        ('data_breach', 'Data Breach Attempt'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('system_compromise', 'System Compromise'),
    )
    
    SEVERITY_LEVELS = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )
    
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Incident details
    title = models.CharField(max_length=200)
    description = models.TextField()
    affected_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    
    # Response
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(null=True, blank=True)
    resolved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_incidents')
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_incident_type_display()} - {self.get_severity_display()}"


# Reporting and Analytics
class Report(models.Model):
    """System reports and analytics"""
    REPORT_TYPES = (
        ('daily_summary', 'Daily Summary'),
        ('weekly_summary', 'Weekly Summary'),
        ('monthly_summary', 'Monthly Summary'),
        ('application_status', 'Application Status Report'),
        ('processing_time', 'Processing Time Analysis'),
        ('fee_collection', 'Fee Collection Report'),
        ('user_activity', 'User Activity Report'),
    )
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=200)
    
    # Report parameters
    date_from = models.DateField()
    date_to = models.DateField()
    filters = models.JSONField(default=dict)
    
    # Report data
    data = models.JSONField()
    file_path = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Generation details
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.date_from} to {self.date_to}"