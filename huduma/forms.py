# forms.py
from django import forms
from .models import BirthCertificate


class BirthCertificateForm(forms.ModelForm):
    class Meta:
        model = BirthCertificate
        fields = [
            # Identifiers
            "certificate_number", "serial_number",

            # Personal Info
            "full_name", "date_of_birth", "place_of_birth", "gender",

            # Birth Location
            "county_of_birth", "sub_county_of_birth", "division_of_birth",
            "location_of_birth", "sub_location_of_birth", "village_of_birth",

            # Family Info
            "father_name", "father_id", "father_nationality",
            "mother_name", "mother_id", "mother_nationality",
            "guardian_name", "guardian_id", "guardian_relationship",

            # Registration Details
            "registration_date", "issuing_office", "registrar_name",

            # Non-Kenyan
            "is_kenyan_born", "naturalization_cert", "citizenship_acquired_date",

            # Status
            "is_active", "is_verified"
        ]

        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "registration_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "citizenship_acquired_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "gender": forms.Select(attrs={"class": "form-select"}),
            "county_of_birth": forms.Select(attrs={"class": "form-select"}),
            "sub_county_of_birth": forms.Select(attrs={"class": "form-select"}),
            "division_of_birth": forms.Select(attrs={"class": "form-select"}),
            "location_of_birth": forms.Select(attrs={"class": "form-select"}),
            "sub_location_of_birth": forms.Select(attrs={"class": "form-select"}),
            "village_of_birth": forms.Select(attrs={"class": "form-select"}),

            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "place_of_birth": forms.TextInput(attrs={"class": "form-control"}),

            "father_name": forms.TextInput(attrs={"class": "form-control"}),
            "father_id": forms.TextInput(attrs={"class": "form-control"}),
            "father_nationality": forms.TextInput(attrs={"class": "form-control"}),

            "mother_name": forms.TextInput(attrs={"class": "form-control"}),
            "mother_id": forms.TextInput(attrs={"class": "form-control"}),
            "mother_nationality": forms.TextInput(attrs={"class": "form-control"}),

            "guardian_name": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_id": forms.TextInput(attrs={"class": "form-control"}),
            "guardian_relationship": forms.TextInput(attrs={"class": "form-control"}),

            "issuing_office": forms.TextInput(attrs={"class": "form-control"}),
            "registrar_name": forms.TextInput(attrs={"class": "form-control"}),

            "naturalization_cert": forms.TextInput(attrs={"class": "form-control"}),

            "is_kenyan_born": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_verified": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# national_ids/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import NationalID, IDApplication, County, SubCounty, DOOffice


class NationalIDForm(forms.ModelForm):
    """Form for creating/editing National ID"""
    
    class Meta:
        model = NationalID
        fields = [
            'application', 'full_name', 'date_of_birth', 'place_of_birth', 
            'gender', 'district_of_birth', 'division_of_birth', 
            'location_of_birth', 'sub_location', 'clan', 'place_of_issue',
            'expiry_date', 'photo', 'signature', 'is_active'
        ]
        
        widgets = {
            'application': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name as it appears on birth certificate'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'place_of_birth': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter place of birth'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'district_of_birth': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter district of birth'
            }),
            'division_of_birth': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter division of birth'
            }),
            'location_of_birth': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter location of birth'
            }),
            'sub_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter sub-location'
            }),
            'clan': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter clan name (optional)'
            }),
            'place_of_issue': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter place of issue'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'signature': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'full_name': 'Full Name',
            'date_of_birth': 'Date of Birth',
            'place_of_birth': 'Place of Birth',
            'district_of_birth': 'District of Birth',
            'division_of_birth': 'Division of Birth',
            'location_of_birth': 'Location of Birth',
            'sub_location': 'Sub-Location',
            'clan': 'Clan Name',
            'place_of_issue': 'Place of Issue',
            'expiry_date': 'Expiry Date',
            'photo': 'Passport Photo',
            'signature': 'Signature',
            'is_active': 'Active Status',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter applications that don't have National IDs yet
        self.fields['application'].queryset = IDApplication.objects.filter(
            national_id__isnull=True,
            status='biometrics_taken'
        ).select_related('birth_certificate')
        
        # Make photo required for new IDs
        if not self.instance.pk:
            self.fields['photo'].required = True
    
    def clean_full_name(self):
        full_name = self.cleaned_data['full_name']
        if len(full_name.split()) < 2:
            raise ValidationError("Full name must contain at least first and last name.")
        return full_name.upper()
    
    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError("Photo file size must be less than 5MB.")
        return photo
    
    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if signature:
            if signature.size > 2 * 1024 * 1024:  # 2MB limit
                raise ValidationError("Signature file size must be less than 2MB.")
        return signature


class NationalIDFilterForm(forms.Form):
    """Form for filtering National IDs"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by ID number, name, application number...'
        })
    )
    
    county = forms.ModelChoiceField(
        queryset=County.objects.all().order_by('name'),
        required=False,
        empty_label="All Counties",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    sub_county = forms.ModelChoiceField(
        queryset=SubCounty.objects.all().order_by('name'),
        required=False,
        empty_label="All Sub Counties",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    gender = forms.ChoiceField(
        choices=[('', 'All Genders'), ('M', 'Male'), ('F', 'Female')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Active'), ('false', 'Inactive')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_collected = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Collected'), ('false', 'Not Collected')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_printed = forms.ChoiceField(
        choices=[('', 'All'), ('true', 'Printed'), ('false', 'Not Printed')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class BulkActionForm(forms.Form):
    """Form for bulk actions on National IDs"""
    
    ACTION_CHOICES = [
        ('mark_printed', 'Mark as Printed'),
        ('mark_dispatched', 'Mark as Dispatched'),
        ('mark_ready_collection', 'Mark Ready for Collection'),
        ('deactivate', 'Deactivate'),
        ('activate', 'Activate'),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    selected_ids = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I confirm that I want to perform this action on the selected National IDs"
    )



from django import forms
from .models import WaitingCard, DOOffice


class WaitingCardForm(forms.ModelForm):
    """Form for updating waiting card details"""
    
    class Meta:
        model = WaitingCard
        fields = [
            'expected_collection_date',
            'collection_location',
            'collection_instructions',
            'is_active',
            'is_collected'
        ]
        widgets = {
            'expected_collection_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'collection_location': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'collection_instructions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Enter collection instructions for the applicant...'
                }
            ),
            'is_active': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'is_collected': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }
        labels = {
            'expected_collection_date': 'Expected Collection Date',
            'collection_location': 'Collection Location (DO Office)',
            'collection_instructions': 'Collection Instructions',
            'is_active': 'Card is Active',
            'is_collected': 'Mark as Collected',
        }
        help_texts = {
            'expected_collection_date': 'When should the applicant come to collect their ID?',
            'collection_location': 'Which DO Office will handle the ID collection?',
            'collection_instructions': 'Specific instructions for the applicant regarding collection process.',
            'is_active': 'Uncheck to deactivate this waiting card',
            'is_collected': 'Check if the ID has been collected using this waiting card',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter collection locations to only active DO offices
        self.fields['collection_location'].queryset = DOOffice.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Make fields required
        self.fields['expected_collection_date'].required = True
        self.fields['collection_location'].required = True
        self.fields['collection_instructions'].required = True

    def clean_expected_collection_date(self):
        """Validate collection date"""
        expected_date = self.cleaned_data.get('expected_collection_date')
        
        if expected_date:
            from django.utils import timezone
            from datetime import date
            
            # Don't allow dates too far in the past
            if expected_date < date.today():
                raise forms.ValidationError("Collection date cannot be in the past.")
        
        return expected_date

    def clean(self):
        """Additional form validation"""
        cleaned_data = super().clean()
        is_collected = cleaned_data.get('is_collected')
        is_active = cleaned_data.get('is_active')
        
        # If collected, it should still be active
        if is_collected and not is_active:
            raise forms.ValidationError(
                "A collected waiting card should remain active for record keeping."
            )
        
        return cleaned_data
    
# forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import (
    WaitingCard, IDApplication, County, SubCounty, DOOffice,
    CustomUser, DocumentType, Document
)


class WaitingCardFilterForm(forms.Form):
    """Form for filtering waiting cards in the list view"""
    
    COLLECTION_STATUS_CHOICES = [
        ('', 'All'),
        ('collected', 'Collected'),
        ('pending', 'Pending Collection'),
    ]
    
    ACTIVE_STATUS_CHOICES = [
        ('', 'All Status'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Serial number, applicant name, application number...',
            'id': 'search'
        })
    )
    
    collection_location = forms.ModelChoiceField(
        queryset=DOOffice.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Locations",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'collection_location'
        })
    )
    
    county = forms.ModelChoiceField(
        queryset=County.objects.all().order_by('name'),
        required=False,
        empty_label="All Counties",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'county'
        })
    )
    
    sub_county = forms.ModelChoiceField(
        queryset=SubCounty.objects.none(),  # Will be populated via AJAX
        required=False,
        empty_label="All Sub Counties",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'sub_county'
        })
    )
    
    is_active = forms.ChoiceField(
        choices=ACTIVE_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'is_active'
        })
    )
    
    is_collected = forms.ChoiceField(
        choices=COLLECTION_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'is_collected'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'date_from'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'date_to'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate sub_county choices based on county if provided
        if 'data' in kwargs and kwargs['data'].get('county'):
            try:
                county_id = int(kwargs['data']['county'])
                self.fields['sub_county'].queryset = SubCounty.objects.filter(
                    county_id=county_id
                ).order_by('name')
            except (ValueError, TypeError):
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError("Start date cannot be later than end date.")
            
            # Check if date range is too wide (optional validation)
            if (date_to - date_from).days > 365:
                raise ValidationError("Date range cannot exceed 365 days.")
        
        return cleaned_data


class WaitingCardUpdateForm(forms.ModelForm):
    """Form for updating waiting card details"""
    
    class Meta:
        model = WaitingCard
        fields = [
            'expected_collection_date',
            'collection_location',
            'collection_instructions',
            'is_active'
        ]
        widgets = {
            'expected_collection_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'collection_location': forms.Select(attrs={
                'class': 'form-select'
            }),
            'collection_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter collection instructions for the applicant...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter collection locations to only active DO offices
        self.fields['collection_location'].queryset = DOOffice.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Set default collection date to 14 days from now if creating new
        if not self.instance.pk:
            self.fields['expected_collection_date'].initial = (
                timezone.now().date() + timezone.timedelta(days=14)
            )
    
    def clean_expected_collection_date(self):
        collection_date = self.cleaned_data.get('expected_collection_date')
        
        if collection_date:
            # Collection date should not be in the past
            if collection_date < timezone.now().date():
                raise ValidationError("Collection date cannot be in the past.")
            
            # Collection date should not be too far in the future (e.g., max 90 days)
            max_future_date = timezone.now().date() + timezone.timedelta(days=90)
            if collection_date > max_future_date:
                raise ValidationError("Collection date cannot be more than 90 days in the future.")
        
        return collection_date


class WaitingCardCreateForm(forms.ModelForm):
    """Form for creating a new waiting card"""
    
    application = forms.ModelChoiceField(
        queryset=IDApplication.objects.filter(
            status='biometrics_taken',
            waiting_card__isnull=True  # Applications without waiting cards
        ).select_related('applicant'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        empty_label="Select Application"
    )
    
    class Meta:
        model = WaitingCard
        fields = [
            'application',
            'expected_collection_date',
            'collection_location',
            'collection_instructions'
        ]
        widgets = {
            'expected_collection_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'collection_location': forms.Select(attrs={
                'class': 'form-select'
            }),
            'collection_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter collection instructions for the applicant...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter collection locations to only active DO offices
        self.fields['collection_location'].queryset = DOOffice.objects.filter(
            is_active=True
        ).order_by('name')
        
        # Set default collection date
        self.fields['expected_collection_date'].initial = (
            timezone.now().date() + timezone.timedelta(days=14)
        )
        
        # Set default collection instructions
        self.fields['collection_instructions'].initial = (
            "Please bring this waiting card and a copy of your National ID application "
            "receipt when collecting your ID. Collection hours: Monday-Friday 8:00AM-5:00PM."
        )
    
    def clean_application(self):
        application = self.cleaned_data.get('application')
        
        if application:
            # Check if application already has a waiting card
            if hasattr(application, 'waiting_card'):
                raise ValidationError("This application already has a waiting card.")
            
            # Check if application status is appropriate
            if application.status != 'biometrics_taken':
                raise ValidationError(
                    "Waiting card can only be created for applications with 'biometrics_taken' status."
                )
            
            # Check if biometric data exists
            if not hasattr(application, 'biometric_data'):
                raise ValidationError(
                    "Application must have biometric data before creating waiting card."
                )
        
        return application


class WaitingCardCollectionForm(forms.Form):
    """Form for marking a waiting card as collected"""
    
    collector_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Full name of person collecting the ID'
        }),
        help_text="Enter the full name of the person collecting the ID"
    )
    
    collector_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'National ID number of collector'
        }),
        help_text="Enter the National ID number of the person collecting"
    )
    
    relationship_to_applicant = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Self, Parent, Guardian, Spouse'
        }),
        help_text="Relationship to the applicant (if not collecting personally)"
    )
    
    authorization_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png'
        }),
        help_text="Upload authorization letter if collected by someone else"
    )
    
    collection_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional notes about the collection...'
        }),
        required=False,
        help_text="Optional notes about the collection process"
    )
    
    confirm_collection = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="I confirm that the waiting card has been collected and the applicant has been informed about ID collection procedures."
    )
    
    def clean(self):
        cleaned_data = super().clean()
        collector_name = cleaned_data.get('collector_name')
        relationship = cleaned_data.get('relationship_to_applicant')
        authorization_doc = cleaned_data.get('authorization_document')
        
        # If relationship indicates someone else is collecting, require authorization
        if relationship and relationship.lower() not in ['self', '']:
            if not authorization_doc:
                raise ValidationError(
                    "Authorization document is required when ID is collected by someone other than the applicant."
                )
        
        return cleaned_data


class WaitingCardSearchForm(forms.Form):
    """Quick search form for waiting cards"""
    
    SEARCH_TYPE_CHOICES = [
        ('serial', 'Serial Number'),
        ('application', 'Application Number'),
        ('applicant', 'Applicant Name'),
        ('phone', 'Phone Number'),
    ]
    
    search_type = forms.ChoiceField(
        choices=SEARCH_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    search_value = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter search value...'
        })
    )
    
    def clean_search_value(self):
        search_value = self.cleaned_data.get('search_value')
        search_type = self.cleaned_data.get('search_type')
        
        if search_value:
            search_value = search_value.strip()
            
            # Validate based on search type
            if search_type == 'serial' and len(search_value) < 3:
                raise ValidationError("Serial number must be at least 3 characters.")
            
            if search_type == 'phone':
                # Basic phone validation
                if not search_value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                    raise ValidationError("Please enter a valid phone number.")
        
        return search_value


class WaitingCardBulkActionForm(forms.Form):
    """Form for bulk actions on waiting cards"""
    
    BULK_ACTIONS = [
        ('', 'Select Action'),
        ('mark_collected', 'Mark as Collected'),
        ('mark_active', 'Mark as Active'),
        ('mark_inactive', 'Mark as Inactive'),
        ('update_collection_date', 'Update Collection Date'),
        ('export_selected', 'Export Selected'),
    ]
    
    action = forms.ChoiceField(
        choices=BULK_ACTIONS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    selected_cards = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    
    # Additional fields for specific actions
    new_collection_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="New collection date (for update collection date action)"
    )
    
    bulk_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes for this bulk action...'
        }),
        required=False,
        help_text="Optional notes explaining the bulk action"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        selected_cards = cleaned_data.get('selected_cards')
        new_collection_date = cleaned_data.get('new_collection_date')
        
        if action and not selected_cards:
            raise ValidationError("Please select at least one waiting card.")
        
        if action == 'update_collection_date' and not new_collection_date:
            raise ValidationError("New collection date is required for this action.")
        
        if new_collection_date and new_collection_date < timezone.now().date():
            raise ValidationError("New collection date cannot be in the past.")
        
        return cleaned_data


class WaitingCardReportForm(forms.Form):
    """Form for generating waiting card reports"""
    
    REPORT_TYPES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('collection_due', 'Collection Due Report'),
        ('overdue', 'Overdue Collection Report'),
        ('county_breakdown', 'County Breakdown Report'),
    ]
    
    EXPORT_FORMATS = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMATS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Report period start date"
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text="Report period end date"
    )
    
    county_filter = forms.ModelChoiceField(
        queryset=County.objects.all().order_by('name'),
        required=False,
        empty_label="All Counties",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    collection_location_filter = forms.ModelChoiceField(
        queryset=DOOffice.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Collection Locations",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    include_collected = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Include already collected cards"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set default date range (last 30 days)
        today = timezone.now().date()
        self.fields['date_to'].initial = today
        self.fields['date_from'].initial = today - timezone.timedelta(days=30)
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError("Start date cannot be later than end date.")
            
            if date_to > timezone.now().date():
                raise ValidationError("End date cannot be in the future.")
        
        return cleaned_data


class WaitingCardVerificationForm(forms.Form):
    """Form for verifying waiting card authenticity"""
    
    serial_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter waiting card serial number',
            'style': 'text-transform: uppercase;'
        }),
        help_text="Enter the serial number printed on the waiting card"
    )
    
    verification_code = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter verification code (optional)'
        }),
        help_text="Verification code from QR code scan (optional)"
    )
    
    def clean_serial_number(self):
        serial_number = self.cleaned_data.get('serial_number')
        
        if serial_number:
            serial_number = serial_number.strip().upper()
            
            # Check if waiting card exists
            try:
                waiting_card = WaitingCard.objects.get(serial_number=serial_number)
                self.waiting_card = waiting_card
            except WaitingCard.DoesNotExist:
                raise ValidationError("No waiting card found with this serial number.")
        
        return serial_number
    
    def get_waiting_card(self):
        """Return the found waiting card after form validation"""
        return getattr(self, 'waiting_card', None)


class WaitingCardCollectionStatusForm(forms.Form):
    """Form for updating collection status of multiple cards"""
    
    waiting_cards = forms.ModelMultipleChoiceField(
        queryset=WaitingCard.objects.filter(is_collected=False),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        })
    )
    
    mark_as_collected = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Mark selected cards as collected"
    )
    
    collection_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter notes about the collection...'
        }),
        required=False,
        help_text="Optional notes about the bulk collection"
    )
    
    def __init__(self, *args, **kwargs):
        collection_location = kwargs.pop('collection_location', None)
        super().__init__(*args, **kwargs)
        
        # Filter waiting cards by collection location if provided
        if collection_location:
            self.fields['waiting_cards'].queryset = WaitingCard.objects.filter(
                collection_location=collection_location,
                is_collected=False
            ).order_by('expected_collection_date')


class NameChangeApprovalForm(forms.Form):
    """Form for approving name change requests"""
    
    approval_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Enter notes about the approval decision...'
        }),
        required=False,
        help_text="Optional notes explaining the approval decision"
    )
    
    confirm_approval = forms.BooleanField(
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="I confirm that I have reviewed all documents and approve this name change request."
    )
    
    notify_applicant = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Send notification to applicant"
    )


class NameChangeRejectionForm(forms.Form):
    """Form for rejecting name change requests"""
    
    REJECTION_REASONS = [
        ('insufficient_documentation', 'Insufficient Documentation'),
        ('invalid_documents', 'Invalid or Fraudulent Documents'),
        ('name_not_acceptable', 'Proposed Name Not Acceptable'),
        ('duplicate_request', 'Duplicate Request'),
        ('technical_error', 'Technical Error in Application'),
        ('legal_issues', 'Legal Issues with Request'),
        ('other', 'Other (specify in notes)'),
    ]
    
    rejection_reason = forms.ChoiceField(
        choices=REJECTION_REASONS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Select the primary reason for rejection"
    )
    
    rejection_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Provide detailed explanation for the rejection...'
        }),
        help_text="Detailed explanation that will be sent to the applicant"
    )
    
    allow_resubmission = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Allow applicant to resubmit with corrections"
    )
    
    notify_applicant = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label="Send notification to applicant"
    )
    
    def clean_rejection_notes(self):
        notes = self.cleaned_data.get('rejection_notes')
        
        if not notes or len(notes.strip()) < 10:
            raise ValidationError("Please provide a detailed explanation for the rejection.")
        
        return notes.strip()


class DocumentVerificationForm(forms.Form):
    """Form for verifying documents attached to applications"""
    
    VERIFICATION_ACTIONS = [
        ('verify', 'Verify Document'),
        ('unverify', 'Mark as Unverified'),
        ('request_resubmission', 'Request Resubmission'),
    ]
    
    action = forms.ChoiceField(
        choices=VERIFICATION_ACTIONS,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    verification_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter verification notes...'
        }),
        required=False,
        help_text="Notes about the document verification"
    )
    
    quality_score = forms.IntegerField(
        min_value=0,
        max_value=100,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0-100'
        }),
        help_text="Document quality score (0-100)"
    )
    
    def clean_verification_notes(self):
        action = self.cleaned_data.get('action')
        notes = self.cleaned_data.get('verification_notes')
        
        # Require notes for certain actions
        if action in ['unverify', 'request_resubmission'] and not notes:
            raise ValidationError("Verification notes are required for this action.")
        
        return notes