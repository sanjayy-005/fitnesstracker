from django.core.validators import RegexValidator

# 10 to 13 digits, with an optional leading "+" (e.g. 9876543210 or +919876543210).
phone_validator = RegexValidator(
    regex=r"^\+?[0-9]{10,13}$",
    message="Enter a valid phone number (10 to 13 digits, optional leading +).",
)
