import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from huduma.models import (
    County, SubCounty, Division, Location, SubLocation, Village,
    CustomUser, BirthCertificate, IDApplication, NationalID,
    ChiefOffice, Chief, DOOffice, DOOfficer, BiometricData,
    ApplicationStatusHistory
)
from decimal import Decimal


class Command(BaseCommand):
    help = 'Generate 100 National IDs with real Kenyan names'

    def __init__(self):
        super().__init__()
        
        # Real Kenyan names by ethnic groups
        self.kenyan_names = {
            'kikuyu': {
                'male': ['Kamau', 'Mwangi', 'Wanjiku', 'Njoroge', 'Karanja', 'Maina', 'Njenga', 'Githui', 'Mungai', 'Thuo'],
                'female': ['Wanjiku', 'Njeri', 'Wangari', 'Wambui', 'Nyokabi', 'Wairimu', 'Wanjiru', 'Nyambura', 'Muthoni', 'Wangechi'],
                'surnames': ['Kamau', 'Mwangi', 'Njoroge', 'Karanja', 'Maina', 'Njenga', 'Githui', 'Mungai', 'Thuo', 'Kariuki']
            },
            'luo': {
                'male': ['Ochieng', 'Otieno', 'Owino', 'Ouma', 'Okoth', 'Odongo', 'Omondi', 'Ogola', 'Onyango', 'Awino'],
                'female': ['Akinyi', 'Awino', 'Adhiambo', 'Atieno', 'Akello', 'Apiyo', 'Awuor', 'Achieng', 'Anyango', 'Abongo'],
                'surnames': ['Ochieng', 'Otieno', 'Owino', 'Ouma', 'Okoth', 'Odongo', 'Omondi', 'Ogola', 'Onyango', 'Awino']
            },
            'luhya': {
                'male': ['Wekesa', 'Wafula', 'Barasa', 'Mukoya', 'Wamalwa', 'Wanjala', 'Wanyonyi', 'Mukhwana', 'Wanyama', 'Simiyu'],
                'female': ['Nekesa', 'Nafula', 'Nasimiyu', 'Nanjala', 'Namukoya', 'Namalwa', 'Nanyonyi', 'Nangila', 'Nasike', 'Namaemba'],
                'surnames': ['Wekesa', 'Wafula', 'Barasa', 'Mukoya', 'Wamalwa', 'Wanjala', 'Wanyonyi', 'Mukhwana', 'Wanyama', 'Simiyu']
            },
            'kalenjin': {
                'male': ['Kiprop', 'Kirui', 'Kiptoo', 'Rotich', 'Bett', 'Koech', 'Lagat', 'Kiprotich', 'Ruto', 'Sang'],
                'female': ['Jebet', 'Chepng\'eno', 'Cheruto', 'Cheptoo', 'Chebet', 'Jepkorir', 'Jepkemboi', 'Chepkemei', 'Jepleting', 'Chepchumba'],
                'surnames': ['Kiprop', 'Kirui', 'Kiptoo', 'Rotich', 'Bett', 'Koech', 'Lagat', 'Kiprotich', 'Ruto', 'Sang']
            },
            'kamba': {
                'male': ['Mutua', 'Musyoka', 'Mwanzia', 'Mutinda', 'Kyalo', 'Mutunga', 'Ndunda', 'Mutuku', 'Muthama', 'Nganga'],
                'female': ['Mumbua', 'Kavata', 'Wayua', 'Nduku', 'Mbula', 'Mueni', 'Kalondu', 'Katunge', 'Mwende', 'Mukui'],
                'surnames': ['Mutua', 'Musyoka', 'Mwanzia', 'Mutinda', 'Kyalo', 'Mutunga', 'Ndunda', 'Mutuku', 'Muthama', 'Nganga']
            }
        }
        
        # Kenyan counties
        self.kenyan_counties = [
            'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Uasin Gishu', 'Machakos',
            'Kiambu', 'Meru', 'Kakamega', 'Murang\'a', 'Nyeri', 'Laikipia',
            'Kericho', 'Bomet', 'Nandi', 'Baringo', 'Elgeyo-Marakwet', 'Kajiado',
            'Kirinyaga', 'Nyandarua', 'Embu', 'Tharaka-Nithi', 'Kitui', 'Makueni'
        ]
        
        # Common Kenyan locations
        self.locations_data = {
            'Nairobi': ['Westlands', 'Kasarani', 'Embakasi', 'Dagoretti', 'Langata', 'Starehe'],
            'Mombasa': ['Mvita', 'Changamwe', 'Jomba', 'Kisauni', 'Nyali', 'Likoni'],
            'Kisumu': ['Kisumu East', 'Kisumu West', 'Kisumu Central', 'Seme', 'Nyando', 'Muhoroni'],
            'Nakuru': ['Nakuru Town', 'Njoro', 'Molo', 'Gilgil', 'Naivasha', 'Kuresoi'],
            'Kiambu': ['Thika', 'Kikuyu', 'Limuru', 'Gatundu', 'Lari', 'Githunguri']
        }

    def create_location_hierarchy(self):
        """Create basic location hierarchy for Kenya"""
        self.stdout.write('Creating location hierarchy...')
        
        counties = {}
        sub_counties = {}
        divisions = {}
        locations = {}
        sub_locations = {}
        villages = {}
        
        # Create counties
        for county_name in self.kenyan_counties[:10]:  # Use first 10 counties
            county, created = County.objects.get_or_create(
                name=county_name,
                defaults={'code': county_name[:3].upper()}
            )
            counties[county_name] = county
            
            # Create sub-counties
            locations_list = self.locations_data.get(county_name, ['Central', 'North', 'South'])
            for i, loc_name in enumerate(locations_list[:3]):  # 3 sub-counties per county
                sub_county_name = f"{loc_name} Sub-County"
                sub_county_code = f"{county.code}{i+1:02d}"
                
                # Use get_or_create with unique fields to avoid duplicates
                sub_county, created = SubCounty.objects.get_or_create(
                    county=county,
                    code=sub_county_code,
                    defaults={'name': sub_county_name}
                )
                sub_counties[f"{county_name}_{loc_name}"] = sub_county
                
                # Create divisions
                for j in range(2):  # 2 divisions per sub-county
                    division, created = Division.objects.get_or_create(
                        name=f"{loc_name} Division {j+1}",
                        sub_county=sub_county
                    )
                    divisions[f"{county_name}_{loc_name}_{j}"] = division
                    
                    # Create locations
                    for k in range(2):  # 2 locations per division
                        location, created = Location.objects.get_or_create(
                            name=f"{loc_name} Location {k+1}",
                            division=division
                        )
                        locations[f"{county_name}_{loc_name}_{j}_{k}"] = location
                        
                        # Create sub-locations
                        for l in range(2):  # 2 sub-locations per location
                            sub_location, created = SubLocation.objects.get_or_create(
                                name=f"{loc_name} Sub-Location {l+1}",
                                location=location
                            )
                            sub_locations[f"{county_name}_{loc_name}_{j}_{k}_{l}"] = sub_location
                            
                            # Create villages
                            for m in range(3):  # 3 villages per sub-location
                                village, created = Village.objects.get_or_create(
                                    name=f"{loc_name} Village {m+1}",
                                    sub_location=sub_location
                                )
                                villages[f"{county_name}_{loc_name}_{j}_{k}_{l}_{m}"] = village
        
        return counties, sub_counties, divisions, locations, sub_locations, villages

    def create_administrative_structure(self, counties, locations, sub_locations):
        """Create chief offices, DO offices, and staff"""
        self.stdout.write('Creating administrative structure...')
        
        chief_offices = []
        do_offices = []
        
        # Create DO offices (one per county)
        for county_name, county in list(counties.items())[:5]:  # First 5 counties
            do_office, created = DOOffice.objects.get_or_create(
                name=f"{county_name} DO Office",
                county=county,
                defaults={
                    'address': f"P.O. Box 123, {county_name}",
                    'contact_phone': f"+254{random.randint(700000000, 799999999)}",
                    'email': f"do.{county_name.lower().replace(' ', '')}@gov.ke",
                    'postal_address': f"P.O. Box {random.randint(100, 999)}, {county_name}"
                }
            )
            do_offices.append(do_office)
            
            # Create DO Officer
            if not hasattr(do_office, 'officers') or not do_office.officers.exists():
                # Create user for DO Officer
                username = f"do_{county_name.lower().replace(' ', '_')}"
                user, created = CustomUser.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': random.choice(['John', 'Mary', 'David', 'Grace']),
                        'last_name': random.choice(['Kiprotich', 'Wanjiku', 'Ochieng', 'Mutua']),
                        'email': f"{username}@gov.ke",
                        'user_type': 'do_officer',
                        'county': county,
                        'is_verified': True,
                        'password': make_password('password123')
                    }
                )
                
                do_officer, created = DOOfficer.objects.get_or_create(
                    user=user,
                    defaults={
                        'do_office': do_office,
                        'employee_id': f"DO{random.randint(1000, 9999)}",
                        'appointment_date': date.today() - timedelta(days=random.randint(365, 1825))
                    }
                )
        
        # Create chief offices (multiple per county)
        location_keys = list(locations.keys())[:15]  # First 15 locations
        for loc_key in location_keys:
            location = locations[loc_key]
            # Find a sub-location in this location
            sub_loc_keys = [k for k in sub_locations.keys() if k.startswith('_'.join(loc_key.split('_')[:4]))]
            if sub_loc_keys:
                sub_location = sub_locations[sub_loc_keys[0]]
                
                chief_office, created = ChiefOffice.objects.get_or_create(
                    name=f"{location.name} Chief Office",
                    location=location,
                    sub_location=sub_location,
                    defaults={
                        'address': f"Chief's Camp, {location.name}",
                        'contact_phone': f"+254{random.randint(700000000, 799999999)}"
                    }
                )
                chief_offices.append(chief_office)
                
                # Create Chief
                if not hasattr(chief_office, 'chiefs') or not chief_office.chiefs.exists():
                    username = f"chief_{location.name.lower().replace(' ', '_')}"
                    user, created = CustomUser.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': random.choice(['Samuel', 'Margaret', 'Joseph', 'Faith']),
                            'last_name': random.choice(['Kiplagat', 'Njeri', 'Onyango', 'Mwangi']),
                            'email': f"{username}@gov.ke",
                            'user_type': 'chief',
                            'county': location.division.sub_county.county,
                            'is_verified': True,
                            'password': make_password('password123')
                        }
                    )
                    
                    chief, created = Chief.objects.get_or_create(
                        user=user,
                        defaults={
                            'office': chief_office,
                            'employee_id': f"CH{random.randint(1000, 9999)}",
                            'stamp_serial': f"ST{random.randint(10000, 99999)}",
                            'appointment_date': date.today() - timedelta(days=random.randint(365, 1825))
                        }
                    )
        
        return chief_offices, do_offices

    def generate_person_data(self):
        """Generate realistic person data"""
        # Choose ethnic group
        ethnic_group = random.choice(list(self.kenyan_names.keys()))
        names_data = self.kenyan_names[ethnic_group]
        
        # Generate gender and name
        gender = random.choice(['M', 'F'])
        if gender == 'M':
            first_name = random.choice(names_data['male'])
        else:
            first_name = random.choice(names_data['female'])
        
        middle_name = random.choice(names_data['male'] + names_data['female'])
        last_name = random.choice(names_data['surnames'])
        
        full_name = f"{first_name} {middle_name} {last_name}"
        
        # Generate birth date (18-80 years old)
        birth_year = random.randint(date.today().year - 80, date.today().year - 18)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = date(birth_year, birth_month, birth_day)
        
        # Generate phone number
        phone_number = f"+254{random.randint(700000000, 799999999)}"
        
        return {
            'full_name': full_name,
            'first_name': first_name,
            'middle_name': middle_name,
            'last_name': last_name,
            'gender': gender,
            'date_of_birth': birth_date,
            'phone_number': phone_number,
            'ethnic_group': ethnic_group
        }

    def create_users_and_birth_certificates(self, locations, sub_locations, villages):
        """Create users and their birth certificates"""
        self.stdout.write('Creating users and birth certificates...')
        
        users = []
        birth_certificates = []
        
        location_keys = list(locations.keys())
        sub_location_keys = list(sub_locations.keys())
        village_keys = list(villages.keys())
        
        for i in range(100):
            person_data = self.generate_person_data()
            
            # Create user
            username = f"citizen_{i+1:03d}"
            user, created = CustomUser.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': person_data['first_name'],
                    'last_name': person_data['last_name'],
                    'email': f"{username}@example.com",
                    'user_type': 'mwananchi',
                    'phone_number': person_data['phone_number'],
                    'national_id': None,  # Will be set after ID generation
                    'is_verified': True,
                    'password': make_password('password123')
                }
            )
            users.append(user)
            
            # Select random locations for birth
            birth_location_key = random.choice(location_keys)
            birth_location = locations[birth_location_key]
            
            birth_sub_location_key = random.choice([k for k in sub_location_keys 
                                                  if k.startswith('_'.join(birth_location_key.split('_')[:4]))])
            birth_sub_location = sub_locations[birth_sub_location_key]
            
            birth_village_key = random.choice([k for k in village_keys 
                                             if k.startswith('_'.join(birth_sub_location_key.split('_')[:5]))])
            birth_village = villages[birth_village_key]
            
            # Generate parents' names
            parent_ethnic = person_data['ethnic_group']
            parent_names = self.kenyan_names[parent_ethnic]
            
            father_name = f"{random.choice(parent_names['male'])} {random.choice(parent_names['surnames'])}"
            mother_name = f"{random.choice(parent_names['female'])} {random.choice(parent_names['surnames'])}"
            
            # Create birth certificate
            cert_number = f"BC{random.randint(1000000, 9999999)}"
            while BirthCertificate.objects.filter(certificate_number=cert_number).exists():
                cert_number = f"BC{random.randint(1000000, 9999999)}"
            
            birth_cert, created = BirthCertificate.objects.get_or_create(
                certificate_number=cert_number,
                defaults={
                    'full_name': person_data['full_name'],
                    'date_of_birth': person_data['date_of_birth'],
                    'place_of_birth': f"{birth_village.name}, {birth_location.division.sub_county.name}",
                    'gender': person_data['gender'],
                    'county_of_birth': birth_location.division.sub_county.county,
                    'sub_county_of_birth': birth_location.division.sub_county,
                    'division_of_birth': birth_location.division,
                    'location_of_birth': birth_location,
                    'sub_location_of_birth': birth_sub_location,
                    'village_of_birth': birth_village,
                    'father_name': father_name,
                    'father_id': f"{random.randint(10000000, 99999999)}",
                    'mother_name': mother_name,
                    'mother_id': f"{random.randint(10000000, 99999999)}",
                    'registration_date': person_data['date_of_birth'] + timedelta(days=random.randint(30, 365)),
                    'issuing_office': f"{birth_location.division.sub_county.county.name} Registrar Office",
                    'registrar_name': f"Registrar {random.choice(['John', 'Mary', 'David', 'Grace'])} {random.choice(['Kiprotich', 'Wanjiku'])}"
                }
            )
            birth_certificates.append(birth_cert)
        
        return users, birth_certificates

    def create_applications_and_ids(self, users, birth_certificates, locations, sub_locations, 
                                   villages, chief_offices, do_offices):
        """Create ID applications and National IDs"""
        self.stdout.write('Creating ID applications and National IDs...')
        
        applications = []
        national_ids = []
        
        location_keys = list(locations.keys())
        sub_location_keys = list(sub_locations.keys())
        village_keys = list(villages.keys())
        
        for i, (user, birth_cert) in enumerate(zip(users, birth_certificates)):
            # Select random current location (can be different from birth location)
            current_location_key = random.choice(location_keys)
            current_location = locations[current_location_key]
            
            current_sub_location_key = random.choice([k for k in sub_location_keys 
                                                    if k.startswith('_'.join(current_location_key.split('_')[:4]))])
            current_sub_location = sub_locations[current_sub_location_key]
            
            current_village_key = random.choice([k for k in village_keys 
                                               if k.startswith('_'.join(current_sub_location_key.split('_')[:5]))])
            current_village = villages[current_village_key]
            
            # Select chief office and DO office
            chief_office = random.choice(chief_offices)
            do_office = random.choice(do_offices)
            chief = chief_office.chiefs.first()
            do_officer = do_office.officers.first()
            
            # Create ID application
            application = IDApplication.objects.create(
                applicant=user,
                birth_certificate=birth_cert,
                application_type='new',
                entry_point='chief',
                status='collected',  # Complete status
                
                # Personal details from birth certificate
                full_name=birth_cert.full_name,
                date_of_birth=birth_cert.date_of_birth,
                place_of_birth=birth_cert.place_of_birth,
                gender=birth_cert.gender,
                
                # Birth location
                county_of_birth=birth_cert.county_of_birth,
                sub_county_of_birth=birth_cert.sub_county_of_birth,
                division_of_birth=birth_cert.division_of_birth,
                location_of_birth=birth_cert.location_of_birth,
                sub_location_of_birth=birth_cert.sub_location_of_birth,
                village_of_birth=birth_cert.village_of_birth,
                
                # Current location
                current_county=current_location.division.sub_county.county,
                current_sub_county=current_location.division.sub_county,
                current_division=current_location.division,
                current_location=current_location,
                current_sub_location=current_sub_location,
                current_village=current_village,
                
                # Family info
                father_name=birth_cert.father_name,
                father_id=birth_cert.father_id,
                mother_name=birth_cert.mother_name,
                mother_id=birth_cert.mother_id,
                
                # Contact
                phone_number=user.phone_number,
                email=user.email,
                
                # Processing info
                chief_office=chief_office,
                chief=chief,
                do_office=do_office,
                do_officer=do_officer,
                
                submitted_at=timezone.now() - timedelta(days=random.randint(30, 180)),
                approved_at=timezone.now() - timedelta(days=random.randint(1, 30))
            )
            applications.append(application)
            
            # Create National ID
            id_number = f"{random.randint(10000000, 99999999)}"
            while NationalID.objects.filter(id_number=id_number).exists():
                id_number = f"{random.randint(10000000, 99999999)}"
            
            national_id = NationalID.objects.create(
                application=application,
                id_number=id_number,
                full_name=application.full_name,
                date_of_birth=application.date_of_birth,
                place_of_birth=application.place_of_birth,
                gender=application.gender,
                district_of_birth=application.county_of_birth.name,  # Legacy field
                division_of_birth=application.division_of_birth.name,
                location_of_birth=application.location_of_birth.name,
                sub_location=application.sub_location_of_birth.name,
                place_of_issue=do_office.name,
                date_of_issue=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                is_active=True,
                is_printed=True,
                is_dispatched=True,
                is_ready_for_collection=True,
                is_collected=True,
                collected_at=timezone.now() - timedelta(days=random.randint(1, 15)),
                collected_by=user,
                collection_location=do_office
            )
            national_ids.append(national_id)
            
            # Update user with National ID number
            user.national_id = id_number
            user.save()
            
            # Create biometric data
            BiometricData.objects.create(
                application=application,
                photo_quality_score=random.randint(85, 100),
                fingerprint_quality_score=random.randint(85, 100),
                signature_quality_score=random.randint(80, 100),
                captured_by=do_officer.user if do_officer else user,
                capture_location=do_office,
                is_verified=True,
                verified_by=do_officer.user if do_officer else user
            )
            
            # Create status history
            ApplicationStatusHistory.objects.create(
                application=application,
                previous_status=None,
                new_status='collected',
                changed_by=user,
                change_reason='ID collection completed',
                location_type='do_office'
            )
        
        return applications, national_ids

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting National ID generation...'))
        
        # Create location hierarchy
        counties, sub_counties, divisions, locations, sub_locations, villages = self.create_location_hierarchy()
        
        # Create administrative structure
        chief_offices, do_offices = self.create_administrative_structure(counties, locations, sub_locations)
        
        # Create users and birth certificates
        users, birth_certificates = self.create_users_and_birth_certificates(locations, sub_locations, villages)
        
        # Create applications and National IDs
        applications, national_ids = self.create_applications_and_ids(
            users, birth_certificates, locations, sub_locations, villages, 
            chief_offices, do_offices
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully generated:\n'
                f'- {len(counties)} counties\n'
                f'- {len(users)} citizens\n'
                f'- {len(birth_certificates)} birth certificates\n'
                f'- {len(applications)} ID applications\n'
                f'- {len(national_ids)} National IDs\n'
                f'- {len(chief_offices)} chief offices\n'
                f'- {len(do_offices)} DO offices'
            )
        )
        
        # Display sample IDs
        self.stdout.write('\nSample Generated National IDs:')
        self.stdout.write('-' * 60)
        for i, national_id in enumerate(national_ids[:10]):  # Show first 10
            self.stdout.write(
                f'{i+1:2d}. {national_id.id_number} - {national_id.full_name} '
                f'({national_id.gender}, {national_id.date_of_birth})'
            )
        
        self.stdout.write(f'\n... and {len(national_ids) - 10} more IDs')
        self.stdout.write(self.style.SUCCESS('\nGeneration completed successfully!'))