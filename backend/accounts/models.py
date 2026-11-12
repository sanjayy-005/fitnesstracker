from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models

from core.validators import phone_validator


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    STAFF = "STAFF", "Front Desk Staff"
    TRAINER = "TRAINER", "Trainer"
    MEMBER = "MEMBER", "Member"


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # `python manage.py createsuperuser` should always give the ADMIN role.
        extra_fields.setdefault("role", Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Login account. The `role` field drives what each person can do."""

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)
    phone = models.CharField(max_length=15, blank=True, validators=[phone_validator])

    objects = UserManager()

    class Meta:
        ordering = ["username"]

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    def __str__(self):
        return f"{self.username} ({self.role})"
