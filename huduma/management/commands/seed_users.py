from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from huduma.models import County, SubCounty
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed 20 users with real Kenyan names"

    def handle(self, *args, **kwargs):
        # Real Kenyan names
        kenyan_names = [
            "Stephen Ongera", "Mary Wambui", "James Mwangi", "John Odhiambo", "Grace Njeri",
            "Peter Otieno", "Josephine Akinyi", "Samuel Kipchoge", "Caroline Chebet", "Daniel Mutiso",
            "Catherine Wairimu", "Paul Njoroge", "Elizabeth Achieng", "Michael Kimani", "Ann Atieno",
            "David Kiprotich", "Lucy Nyambura", "George Ochieng", "Jane Wanjiru", "Anthony Kiplagat"
        ]

        user_types = [choice[0] for choice in User.USER_TYPES]

        for idx, full_name in enumerate(kenyan_names, start=1):
            first_name, last_name = full_name.split(" ", 1)
            username = f"user{idx}"
            email = f"{first_name.lower()}.{last_name.lower().replace(' ', '')}@example.com"
            phone = f"+2547{random.randint(10000000, 99999999)}"
            nat_id = str(random.randint(10000000, 39999999))

            # Pick a random user type
            user_type = random.choice(user_types)

            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password="cp7kvt",
                    phone_number=phone,
                    national_id=nat_id,
                    user_type=user_type,
                    is_verified=random.choice([True, False]),
                )
                self.stdout.write(self.style.SUCCESS(f"Created {user.username} ({full_name}) as {user_type}"))
            else:
                self.stdout.write(self.style.WARNING(f"{username} already exists"))

        self.stdout.write(self.style.SUCCESS("✅ 20 Kenyan users seeded successfully."))
