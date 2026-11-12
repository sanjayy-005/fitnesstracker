"""
FitTrack - Django settings.

Every value that changes between your laptop and the server (secrets, database
login, allowed websites ...) is read from environment variables. Locally these
come from the `.env` file (copy `.env.example` to `.env`).
"""
import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    """Read a True/False value such as DEBUG=True from the environment."""
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    """Read a comma separated list such as ALLOWED_HOSTS=a.com,b.com."""
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "django-insecure-local-development-key-change-me"
    else:
        raise ImproperlyConfigured("The SECRET_KEY environment variable is required when DEBUG is False.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
# Render sets this variable automatically, so the deployed site is always allowed.
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    # FitTrack apps
    "core",
    "accounts",
    "members",
    "trainers",
    "plans",
    "payments",
    "attendance",
    "dashboard",
    "portal",
    "nutrition",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database (MySQL by default for local development; PostgreSQL is supported for hosting)
# ---------------------------------------------------------------------------
DB_ENGINE = os.getenv("DB_ENGINE", "mysql").strip().lower()

if DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
elif DB_ENGINE in ("postgres", "postgresql"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "fittrack"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "sslmode": os.getenv("DB_SSLMODE", "require"),
            },
        }
    }
elif DB_ENGINE == "mysql":
    # PyMySQL installs on Windows without a C compiler and provides Django's
    # expected MySQLdb interface.
    import pymysql

    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "fittrack"),
            "USER": os.getenv("DB_USER", "root"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
    # Cloud MySQL providers usually require an encrypted connection.
    # Set DB_SSL_CA to a certificate file path to turn it on, e.g.
    # /etc/ssl/certs/ca-certificates.crt on Render.
    _ssl_ca = os.getenv("DB_SSL_CA", "").strip()
    if _ssl_ca:
        _ssl_ca_path = Path(_ssl_ca)
        if not _ssl_ca_path.is_absolute():
            _ssl_ca_path = BASE_DIR / _ssl_ca_path  # relative paths are relative to the backend folder
        DATABASES["default"]["OPTIONS"]["ssl"] = {"ca": str(_ssl_ca_path)}
else:
    raise ImproperlyConfigured(
        "DB_ENGINE must be one of: mysql, postgresql, postgres, or sqlite."
    )

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (served by WhiteNoise in production)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ---------------------------------------------------------------------------
# Django REST Framework + JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardPagination",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "7"))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# CORS / CSRF (which websites may call this API)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")

# ---------------------------------------------------------------------------
# Production security (only when DEBUG is False)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)

# ---------------------------------------------------------------------------
# Gym details printed on payment receipts
# ---------------------------------------------------------------------------
GYM_NAME = os.getenv("GYM_NAME", "FitTrack Gym")
GYM_ADDRESS = os.getenv("GYM_ADDRESS", "12 Fitness Street, Coimbatore, Tamil Nadu 641001")
GYM_PHONE = os.getenv("GYM_PHONE", "+91 98765 43210")
GYM_EMAIL = os.getenv("GYM_EMAIL", "hello@fittrack.example")

# ---------------------------------------------------------------------------
# Food calorie tracking (vision LLM via OpenAI-compatible API)
# ---------------------------------------------------------------------------
FOOD_AI_ENABLED = env_bool("FOOD_AI_ENABLED", True)
FOOD_AI_PROVIDER = os.getenv("FOOD_AI_PROVIDER", "mock").strip().lower()
FOOD_AI_BASE_URL = os.getenv("FOOD_AI_BASE_URL", "https://router.huggingface.co/v1").rstrip("/")
FOOD_AI_MODEL = os.getenv("FOOD_AI_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
FOOD_AI_API_KEY = os.getenv("FOOD_AI_API_KEY", "").strip()
FOOD_AI_STRUCTURED_OUTPUT = os.getenv("FOOD_AI_STRUCTURED_OUTPUT", "json_schema").strip().lower()
FOOD_AI_TIMEOUT_SECONDS = int(os.getenv("FOOD_AI_TIMEOUT_SECONDS", "60"))
FOOD_AI_MAX_IMAGE_PX = int(os.getenv("FOOD_AI_MAX_IMAGE_PX", "1280"))
FOOD_AI_DAILY_SCANS_PER_USER = int(os.getenv("FOOD_AI_DAILY_SCANS_PER_USER", "20"))
