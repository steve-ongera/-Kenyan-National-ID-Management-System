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
