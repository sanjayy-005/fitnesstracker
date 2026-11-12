"""
Load realistic demo data so every screen has something to show.

    python manage.py seed_data            # only runs when the database is empty
    python manage.py seed_data --reset    # wipes everything and loads fresh demo data
"""
import random
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Role
from attendance.models import Attendance
from members.models import Member
from payments.models import Payment
from plans.models import Membership, MembershipPlan
from trainers.models import Trainer

User = get_user_model()

ADMIN_PASSWORD = "Admin@123"
STAFF_PASSWORD = "Staff@123"
TRAINER_PASSWORD = "Trainer@123"
MEMBER_PASSWORD = "Member@123"

PLANS = [
    {
        "name": "Monthly Basic",
        "plan_type": "MONTHLY",
        "price": 1500,
        "description": "Everything you need to start training.",
        "features": "Full gym floor access\nLocker room\nFree fitness assessment",
    },
    {
        "name": "Monthly Plus",
        "plan_type": "MONTHLY",
        "price": 2200,
        "description": "Gym access plus group classes.",
        "features": "Everything in Basic\nYoga, Zumba and HIIT classes\nSteam room",
    },
    {
        "name": "Quarterly Standard",
        "plan_type": "QUARTERLY",
        "price": 4000,
        "description": "Three months of training at a saving.",
        "features": "Full gym floor access\nLocker room\nDiet consultation",
    },
    {
        "name": "Quarterly Pro",
        "plan_type": "QUARTERLY",
        "price": 5500,
        "description": "Three months with personal coaching.",
        "features": "Everything in Standard\nGroup classes\n2 personal training sessions a month",
    },
    {
        "name": "Yearly Premium",
        "plan_type": "YEARLY",
        "price": 14000,
        "description": "Best value - a full year of fitness.",
        "features": "Everything in Quarterly Pro\nFree guest passes\nQuarterly body composition report",
    },
]

# (full name, specialization, years, bio, login username or None)
TRAINERS = [
    ("Arjun Mehta", "Strength & Conditioning", 8, "Powerlifting coach focused on safe, progressive strength.", "arjun"),
    ("Priya Nair", "Yoga & Flexibility", 6, "Certified yoga instructor for mobility and recovery.", "priya"),
    ("Rahul Sharma", "CrossFit", 5, "Functional fitness and high intensity workouts.", "rahul"),
    ("Sneha Iyer", "Cardio & Zumba", 4, "Group class specialist who makes cardio fun.", None),
    ("Karthik Raj", "Bodybuilding", 10, "Competitive bodybuilder and nutrition coach.", None),
]

MALE_FIRST = [
    "Aditya", "Vikram", "Rohan", "Siddharth", "Manoj", "Naveen", "Suresh", "Karan",
    "Deepak", "Harish", "Pranav", "Gokul", "Ashwin", "Tarun", "Varun",
]
FEMALE_FIRST = [
    "Ananya", "Divya", "Kavya", "Meera", "Nisha", "Pooja", "Riya", "Shruti",
    "Swathi", "Tanvi", "Aishwarya", "Lakshmi", "Harini", "Sanjana", "Janani",
]
LAST_NAMES = [
    "Kumar", "Reddy", "Pillai", "Menon", "Gupta", "Verma", "Das", "Joshi",
    "Krishnan", "Bose", "Patel", "Rao", "Shetty", "Chandran", "Subramanian",
]
CITIES = ["Coimbatore", "Tiruppur", "Erode", "Salem", "Pollachi"]
METHODS = ["CASH", "UPI", "UPI", "UPI", "CARD", "BANK_TRANSFER"]


class Command(BaseCommand):
    help = "Create demo users, trainers, plans, members, memberships, payments and attendance."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete all existing data first.")

    def handle(self, *args, **options):
        if options["reset"]:
            self.wipe()
        elif Member.objects.exists() or MembershipPlan.objects.exists() or Trainer.objects.exists():
            self.stdout.write("Data already exists - nothing was changed. Use --reset to wipe and reload.")
            return

        self.rng = random.Random(7)
        self.today = timezone.localdate()

        with transaction.atomic():
            self.create_users()
            plans = self.create_plans()
            trainers = self.create_trainers()
            members = self.create_members(plans, trainers)
            self.create_pending_payments(members)
            self.create_attendance(members)
            self.create_member_login(members[0])
            self.create_demo_meals(members[0])

        self.stdout.write(self.style.SUCCESS("\nDemo data loaded."))
        self.stdout.write("Log in with:")
        self.stdout.write(f"  Admin    -> admin   / {ADMIN_PASSWORD}")
        self.stdout.write(f"  Staff    -> staff   / {STAFF_PASSWORD}")
        self.stdout.write(f"  Trainer  -> arjun   / {TRAINER_PASSWORD}  (also priya, rahul)")
        self.stdout.write(f"  Member   -> member  / {MEMBER_PASSWORD}")

    # ------------------------------------------------------------------
    def wipe(self):
        self.stdout.write("Deleting existing data ...")
        try:
            from nutrition.models import MealEntry, FoodScan

            MealEntry.objects.all().delete()
            FoodScan.objects.all().delete()
        except Exception:
            pass
        Attendance.objects.all().delete()
        Payment.objects.all().delete()
        Membership.objects.all().delete()
        Member.objects.all().delete()
        Trainer.objects.all().delete()
        MembershipPlan.objects.all().delete()
        User.objects.all().delete()

    @staticmethod
    def upsert_user(username, password, **fields):
        user, created = User.objects.get_or_create(username=username, defaults=fields)
        if not created:
            for key, value in fields.items():
                setattr(user, key, value)
        user.set_password(password)
        user.save()
        return user

    def create_users(self):
        self.upsert_user(
            "admin",
            ADMIN_PASSWORD,
            email="admin@fittrack.demo",
            first_name="Aarav",
            last_name="Kapoor",
            role=Role.ADMIN,
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        self.upsert_user(
            "staff",
            STAFF_PASSWORD,
            email="staff@fittrack.demo",
            first_name="Isha",
            last_name="Raman",
            role=Role.STAFF,
            is_active=True,
        )

    def create_plans(self):
        return [MembershipPlan.objects.create(**data) for data in PLANS]

    def create_trainers(self):
        trainers = []
        for index, (name, specialization, years, bio, username) in enumerate(TRAINERS):
            first, _, last = name.partition(" ")
            email = f"{first.lower()}.{last.lower()}@fittrack.demo"
            phone = f"98{index:02d}4{self.rng.randint(10000, 99999)}"
            user = None
            if username:
                user = self.upsert_user(
                    username,
                    TRAINER_PASSWORD,
                    email=email,
                    first_name=first,
                    last_name=last,
                    phone=phone,
                    role=Role.TRAINER,
                    is_active=True,
                )
            trainers.append(
                Trainer.objects.create(
                    user=user,
                    full_name=name,
                    email=email,
                    phone=phone,
                    specialization=specialization,
                    experience_years=years,
                    bio=bio,
                    joined_date=self.today - timedelta(days=self.rng.randint(300, 1500)),
                )
            )
        return trainers

    # ------------------------------------------------------------------
    def add_membership(self, member, plan, start, status=None, payment_status=Payment.Status.PAID):
        end = start + timedelta(days=plan.duration_days - 1)
        if status is None:
            status = Membership.Status.EXPIRED if end < self.today else Membership.Status.ACTIVE
        membership = Membership.objects.create(
            member=member,
            plan=plan,
            start_date=start,
            end_date=end,
            price=plan.price,
            status=status,
        )
        Payment.objects.create(
            member=member,
            membership=membership,
            amount=plan.price,
            method=self.rng.choice(METHODS),
            status=payment_status,
            paid_on=start,
            note=f"{plan.name} membership",
            received_by=User.objects.get(username="staff"),
        )
        return membership

    def create_members(self, plans, trainers):
        rng = self.rng
        today = self.today
        monthly_basic, monthly_plus, quarterly_std, quarterly_pro, yearly = plans
        staff_user = User.objects.get(username="staff")
        members = []

        for i in range(32):
            if i % 2 == 0:
                first, gender = rng.choice(MALE_FIRST), Member.Gender.MALE
            else:
                first, gender = rng.choice(FEMALE_FIRST), Member.Gender.FEMALE
            last = rng.choice(LAST_NAMES)

            member = Member.objects.create(
                full_name=f"{first} {last}",
                email=f"{first.lower()}.{last.lower()}{i + 1}@example.com",
                phone=f"9{rng.randint(0, 999999999):09d}",
                gender=gender,
                date_of_birth=today - timedelta(days=rng.randint(18 * 365, 55 * 365)),
                address=f"{rng.randint(1, 120)}, Gandhi Nagar, {rng.choice(CITIES)}",
                emergency_contact_name=f"{rng.choice(LAST_NAMES)} {rng.choice(['Sr.', 'Family'])}",
                emergency_contact_phone=f"9{rng.randint(0, 999999999):09d}",
                height_cm=rng.randint(150, 190),
                weight_kg=rng.randint(480, 950) / 10,
                trainer=rng.choice(trainers + [None]),
                joined_date=today - timedelta(days=rng.randint(5, 240)),
            )
            members.append(member)

            # ---- scripted cases so every dashboard widget has data ---------------
            if i < 4:  # expiring within the next few days
                start = today + timedelta(days=i) - timedelta(days=29)
                member.joined_date = start
                member.save(update_fields=["joined_date"])
                self.add_membership(member, monthly_basic, start)
            elif i < 7:  # recently expired
                start = today - timedelta(days=5 + i * 3) - timedelta(days=29)
                member.joined_date = start
                member.save(update_fields=["joined_date"])
                self.add_membership(member, monthly_basic, start)
            elif i == 7:  # joined today
                member.joined_date = today
                member.save(update_fields=["joined_date"])
                self.add_membership(member, monthly_plus, today)
            elif i in (8, 9):  # cancelled membership
                start = today - timedelta(days=10)
                member.joined_date = start
                member.save(update_fields=["joined_date"])
                self.add_membership(
                    member,
                    monthly_plus,
                    start,
                    status=Membership.Status.CANCELLED,
                    payment_status=Payment.Status.REFUNDED if i == 8 else Payment.Status.PAID,
                )
            elif i in (10, 11):  # signed up but has not bought a plan yet
                member.joined_date = today - timedelta(days=2)
                member.save(update_fields=["joined_date"])
            else:  # a normal history of renewals
                cursor = member.joined_date
                count = 0
                while cursor <= today and count < 6:
                    plan = rng.choices(plans, weights=[4, 3, 3, 2, 1])[0]
                    membership = self.add_membership(member, plan, cursor)
                    cursor = membership.end_date + timedelta(days=1)
                    count += 1
                    if membership.end_date < today and rng.random() < 0.1:
                        break  # lapsed member

        # Make sure there is a member with a long yearly membership.
        yearly_member = members[12]
        Membership.objects.filter(member=yearly_member).delete()
        Payment.objects.filter(member=yearly_member).delete()
        yearly_member.joined_date = today - timedelta(days=60)
        yearly_member.save(update_fields=["joined_date"])
        self.add_membership(yearly_member, yearly, today - timedelta(days=60))

        self.stdout.write(f"Created {len(members)} members with memberships and payments.")
        return members

    def create_pending_payments(self, members):
        for member in self.rng.sample(members[12:], 3):
            Payment.objects.create(
                member=member,
                amount=self.rng.choice([500, 750, 1000]),
                method="CASH",
                status=Payment.Status.PENDING,
                paid_on=self.today - timedelta(days=2),
                note="Personal training balance",
                received_by=User.objects.get(username="staff"),
            )

    def create_attendance(self, members):
        rng = self.rng
        today = self.today
        now_time = timezone.localtime().time()
        records = []

        for member in members:
            spans = [
                (m.start_date, m.end_date)
                for m in Membership.objects.filter(member=member).exclude(status=Membership.Status.CANCELLED)
            ]
            if not spans:
                continue
            frequency = rng.uniform(0.2, 0.75)

            for days_ago in range(45, -1, -1):
                day = today - timedelta(days=days_ago)
                if day < member.joined_date or not any(s <= day <= e for s, e in spans):
                    continue
                chance = frequency * (0.4 if day.weekday() == 6 else 1.0)
                if rng.random() > chance:
                    continue

                check_in = time(rng.choice([6, 6, 7, 7, 8, 9, 17, 18, 18, 19, 19, 20]), rng.randint(0, 59))
                if day == today and check_in >= now_time:
                    continue  # do not create visits in the future

                if day == today and rng.random() < 0.5:
                    check_out = None  # still inside the gym
                else:
                    finish = datetime.combine(day, check_in) + timedelta(minutes=rng.randint(45, 110))
                    check_out = finish.time() if finish.date() == day else time(23, 59)
                    if day == today and check_out > now_time:
                        check_out = None

                records.append(Attendance(member=member, date=day, check_in=check_in, check_out=check_out))

        Attendance.objects.bulk_create(records)
        self.stdout.write(f"Created {len(records)} attendance records.")

    def create_member_login(self, member):
        first, _, last = member.full_name.partition(" ")
        user = self.upsert_user(
            "member",
            MEMBER_PASSWORD,
            email=member.email,
            first_name=first,
            last_name=last,
            phone=member.phone,
            role=Role.MEMBER,
            is_active=True,
        )
        member.user = user
        member.nutrition_consent_at = timezone.now()
        member.save(update_fields=["user", "nutrition_consent_at"])
        self.stdout.write(f"Linked demo member login to {member.full_name} ({member.member_code}).")

    def create_demo_meals(self, member):
        from decimal import Decimal

        from nutrition.models import MealEntry, MealItem

        today = self.today
        breakfast = MealEntry.objects.create(
            member=member,
            eaten_on=today,
            meal_type=MealEntry.MealType.BREAKFAST,
            source=MealEntry.Source.MANUAL,
            total_kcal=Decimal("320"),
            protein_g=Decimal("14"),
            carbs_g=Decimal("48"),
            fat_g=Decimal("8"),
            fiber_g=Decimal("6"),
            created_by=User.objects.get(username="staff"),
        )
        MealItem.objects.create(
            entry=breakfast,
            name="Idli (2) with sambar",
            quantity=Decimal("1"),
            unit="plate",
            kcal=Decimal("320"),
            protein_g=Decimal("14"),
            carbs_g=Decimal("48"),
            fat_g=Decimal("8"),
            fiber_g=Decimal("6"),
        )
        self.stdout.write("Created sample meal log for the demo member.")
