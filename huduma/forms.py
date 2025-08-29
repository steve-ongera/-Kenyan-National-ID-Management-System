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