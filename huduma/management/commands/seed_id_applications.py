import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from huduma.models import (
    IDApplication, CustomUser, BirthCertificate,
    County, SubCounty, Division, Location, SubLocation, Village
)

from faker import Faker

fake = Faker()  # fallback to default English locale

class Command(BaseCommand):
    help = "Seed 40 random ID Applications"

    def handle(self, *args, **kwargs):
        users = list(CustomUser.objects.all())
        certs = list(BirthCertificate.objects.all())
        counties = list(County.objects.all())

        if not users or not certs or not counties:
            self.stdout.write(self.style.ERROR("⚠ Users, Birth Certificates, or Counties missing. Seed them first."))
            return

        for i in range(40):
            applicant = random.choice(users)
            cert = random.choice(certs)

            # Birth location (from cert)
            county = cert.county_of_birth
            sub_county = cert.sub_county_of_birth
            division = cert.division_of_birth
            location = cert.location_of_birth
            sub_location = cert.sub_location_of_birth
            village = cert.village_of_birth

            # Current residence (random)
            curr_county = random.choice(counties)
            curr_sub = random.choice(curr_county.sub_counties.all())
            curr_div = random.choice(curr_sub.divisions.all())
            curr_loc = random.choice(curr_div.locations.all())
            curr_sub_loc = random.choice(curr_loc.sub_locations.all())
            curr_village = random.choice(curr_sub_loc.villages.all())

            app_type = random.choice([t[0] for t in IDApplication.APPLICATION_TYPES])
            entry_point = random.choice([e[0] for e in IDApplication.ENTRY_POINTS])
            status = random.choice([s[0] for s in IDApplication.APPLICATION_STATUS])

            # Replacement extras
            prev_id = None
            police_ob = None
            police_station = None
            replacement_reason = None
            fee_paid = False
            payment_reference = None

            if app_type == "replacement":
                prev_id = str(random.randint(10000000, 39999999))
                police_ob = f"OB/{random.randint(100, 999)}/{timezone.now().year}"
                police_station = fake.city()
                replacement_reason = random.choice([r[0] for r in IDApplication.REPLACEMENT_REASONS])
                fee_paid = random.choice([True, False])
                if fee_paid:
                    payment_reference = f"MPESA{random.randint(100000,999999)}"

            # Name change extras
            old_name = None
            new_name = None
            name_reason = None
            if app_type == "name_change":
                old_name = cert.full_name
                new_name = fake.name()
                name_reason = random.choice(["Marriage", "Religion", "Personal choice"])

            id_app = IDApplication.objects.create(
                applicant=applicant,
                birth_certificate=cert,

                application_type=app_type,
                entry_point=entry_point,
                status=status,

                full_name=cert.full_name,
                date_of_birth=cert.date_of_birth,
                place_of_birth=cert.place_of_birth,
                gender=cert.gender,

                county_of_birth=county,
                sub_county_of_birth=sub_county,
                division_of_birth=division,
                location_of_birth=location,
                sub_location_of_birth=sub_location,
                village_of_birth=village,

                current_county=curr_county,
                current_sub_county=curr_sub,
                current_division=curr_div,
                current_location=curr_loc,
                current_sub_location=curr_sub_loc,
                current_village=curr_village,

                father_name=cert.father_name,
                father_id=cert.father_id,
                mother_name=cert.mother_name,
                mother_id=cert.mother_id,
                guardian_name=cert.guardian_name,
                guardian_id=cert.guardian_id,
                guardian_relationship=cert.guardian_relationship,

                clan_name=random.choice([None, "Kikuyu", "Luo", "Kalenjin", "Luhya", "Kamba"]),

                phone_number=applicant.phone_number or f"+2547{random.randint(10000000,99999999)}",
                alternative_phone=f"+2547{random.randint(10000000,99999999)}",
                email=applicant.email or fake.email(),
                postal_address=fake.address(),

                # Processing offices left NULL for now
                previous_id_number=prev_id,
                police_ob_number=police_ob,
                police_station=police_station,
                replacement_reason=replacement_reason,
                replacement_fee=Decimal("1000.00"),
                fee_paid=fee_paid,
                payment_reference=payment_reference,

                old_name=old_name,
                new_name=new_name,
                name_change_reason=name_reason,
            )

            self.stdout.write(self.style.SUCCESS(f"[{i+1}/40] Created ID Application {id_app.application_number} ({app_type})"))

        self.stdout.write(self.style.SUCCESS("✅ 40 ID Applications seeded successfully!"))
