from django.core.management.base import BaseCommand
from huduma.models import County, SubCounty, Division, Location, SubLocation, Village

class Command(BaseCommand):
    help = "Seed the database with the 15 largest counties in Kenya and their sub-counties."

    def handle(self, *args, **kwargs):
        counties_data = [
            {
                "name": "Nairobi",
                "code": "047",
                "sub_counties": ["Westlands", "Lang'ata", "Embakasi", "Dagoretti", "Kasarani", "Kamukunji", "Starehe", "Mathare"]
            },
            {
                "name": "Kiambu",
                "code": "022",
                "sub_counties": ["Thika", "Ruiru", "Juja", "Kiambaa", "Limuru", "Githunguri", "Kikuyu"]
            },
            {
                "name": "Nakuru",
                "code": "032",
                "sub_counties": ["Naivasha", "Nakuru Town West", "Nakuru Town East", "Molo", "Gilgil", "Bahati", "Kuresoi"]
            },
            {
                "name": "Kakamega",
                "code": "037",
                "sub_counties": ["Lurambi", "Malava", "Mumias East", "Mumias West", "Lugari", "Ikolomani"]
            },
            {
                "name": "Bungoma",
                "code": "039",
                "sub_counties": ["Kanduyi", "Bumula", "Kimilili", "Tongaren", "Mt Elgon", "Sirisia"]
            },
            {
                "name": "Meru",
                "code": "012",
                "sub_counties": ["Imenti North", "Imenti South", "Buuri", "Tigania East", "Tigania West"]
            },
            {
                "name": "Kisii",
                "code": "045",
                "sub_counties": ["Kitutu Chache North", "Kitutu Chache South", "Nyaribari Masaba", "Bonchari", "Bobasi"]
            },
            {
                "name": "Machakos",
                "code": "016",
                "sub_counties": ["Machakos Town", "Mwala", "Mavoko", "Kangundo", "Kathiani"]
            },
            {
                "name": "Mombasa",
                "code": "001",
                "sub_counties": ["Mvita", "Changamwe", "Jomvu", "Kisauni", "Nyali", "Likoni"]
            },
            {
                "name": "Murang'a",
                "code": "021",
                "sub_counties": ["Kandara", "Kangema", "Kiharu", "Mathioya", "Maragua", "Gatanga"]
            },
            {
                "name": "Uasin Gishu",
                "code": "027",
                "sub_counties": ["Ainabkoi", "Kapseret", "Soy", "Turbo", "Moiben"]
            },
            {
                "name": "Kisumu",
                "code": "042",
                "sub_counties": ["Kisumu East", "Kisumu West", "Kisumu Central", "Muhoroni", "Nyando", "Seme"]
            },
            {
                "name": "Kitui",
                "code": "015",
                "sub_counties": ["Kitui Central", "Kitui East", "Kitui South", "Mwingi Central", "Mwingi North"]
            },
            {
                "name": "Homa Bay",
                "code": "043",
                "sub_counties": ["Kasipul", "Kabondo Kasipul", "Rangwe", "Homa Bay Town", "Ndhiwa", "Suba"]
            },
            {
                "name": "Narok",
                "code": "033",
                "sub_counties": ["Narok North", "Narok South", "Narok East", "Narok West", "Trans Mara East", "Trans Mara West"]
            },
        ]

        for county_data in counties_data:
            county, created = County.objects.get_or_create(
                name=county_data["name"],
                code=county_data["code"]
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Added County: {county.name}"))

            for idx, sc_name in enumerate(county_data["sub_counties"], start=1):
                sub_county, sc_created = SubCounty.objects.get_or_create(
                    name=sc_name,
                    county=county,
                    code=f"{county.code}{idx:02d}"
                )
                if sc_created:
                    self.stdout.write(self.style.SUCCESS(f"  Added SubCounty: {sub_county.name}"))

                # Create placeholder Division, Location, SubLocation, Village
                division, _ = Division.objects.get_or_create(name=f"{sc_name} Division", sub_county=sub_county)
                location, _ = Location.objects.get_or_create(name=f"{sc_name} Location", division=division)
                sub_location, _ = SubLocation.objects.get_or_create(name=f"{sc_name} SubLocation", location=location)
                Village.objects.get_or_create(name=f"{sc_name} Village", sub_location=sub_location)

        self.stdout.write(self.style.SUCCESS("✅ Seeding complete for 15 counties."))
