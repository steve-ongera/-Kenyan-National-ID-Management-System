import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from huduma.models import (
    BirthCertificate, County, SubCounty, Division,
    Location, SubLocation, Village
)

fake = Faker("en_US")  # base locale, but we’ll use Kenyan places

class Command(BaseCommand):
    help = "Seed 400 random birth certificates with Faker"

    def handle(self, *args, **kwargs):
        counties = list(County.objects.all())
        if not counties:
            self.stdout.write(self.style.ERROR("⚠ No counties found! Run seed_counties first."))
            return

        for i in range(400):
            county = random.choice(counties)
            sub_county = random.choice(county.sub_counties.all())
            division = random.choice(sub_county.divisions.all())
            location = random.choice(division.locations.all())
            sub_location = random.choice(location.sub_locations.all())
            village = random.choice(sub_location.villages.all())

            dob = fake.date_of_birth(minimum_age=1, maximum_age=100)
            cert_number = f"CERT-{random.randint(1000000, 9999999)}"

            gender = random.choice(["M", "F"])
            if gender == "M":
                child_name = fake.first_name_male() + " " + fake.last_name()
            else:
                child_name = fake.first_name_female() + " " + fake.last_name()

            # Parents
            father_name = fake.name_male()
            mother_name = fake.name_female()
            guardian_name = random.choice([None, fake.name()])

            birth_cert = BirthCertificate(
                certificate_number=cert_number,
                full_name=child_name,
                date_of_birth=dob,
                place_of_birth=fake.city(),
                gender=gender,

                county_of_birth=county,
                sub_county_of_birth=sub_county,
                division_of_birth=division,
                location_of_birth=location,
                sub_location_of_birth=sub_location,
                village_of_birth=village,

                father_name=father_name,
                father_id=str(random.randint(10000000, 39999999)),
                mother_name=mother_name,
                mother_id=str(random.randint(10000000, 39999999)),

                guardian_name=guardian_name,
                guardian_id=(str(random.randint(10000000, 39999999)) if guardian_name else None),
                guardian_relationship=(random.choice(["Uncle", "Aunt", "Brother", "Sister"]) if guardian_name else None),

                registration_date=fake.date_between(start_date=dob, end_date=timezone.now().date()),
                issuing_office=f"{county.name} Civil Registration Office",
                registrar_name=fake.name(),
                is_kenyan_born=True,
                is_active=True,
                is_verified=True,
            )
            birth_cert.save()

            self.stdout.write(self.style.SUCCESS(f"[{i+1}/400] Created {child_name} ({cert_number})"))

        self.stdout.write(self.style.SUCCESS("✅ 400 Birth Certificates seeded successfully!"))
