"""
إعدادات Django لمشروع thqaf

- اللغة: العربية
- المنطقة الزمنية: الرياض (Asia/Riyadh)
- تحسينات أمان وتهيئة للإنتاج عبر متغيرات البيئة
"""

from pathlib import Path
import os
from typing import List


# =========================
# مسارات المشروع
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# أدوات مساعدة لمتغيرات البيئة
# =========================
def env(name: str, default: str | None = None) -> str | None:
    """قراءة متغير بيئة كنص."""
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    """قراءة متغير بيئة كقيمة منطقية."""
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def env_int(name: str, default: int = 0) -> int:
    """قراءة متغير بيئة كرقم صحيح."""
    val = os.environ.get(name)
    if val is None or not val.strip():
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def env_list(name: str, default: List[str] | None = None, sep: str = ",") -> List[str]:
    """قراءة متغير بيئة كقائمة مفصولة بفواصل."""
    if default is None:
        default = []
    val = os.environ.get(name)
    if not val:
        return default
    return [item.strip() for item in val.split(sep) if item.strip()]


# =========================
# الأمان
# =========================
# في الإنتاج: ضع SECRET_KEY في متغير بيئة ولا تتركه ثابتًا داخل الكود.
SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = env_bool("DJANGO_DEBUG", True)

# أمثلة:
# DJANGO_ALLOWED_HOSTS=example.com,www.example.com,127.0.0.1
ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default=["127.0.0.1", "localhost"] if DEBUG else []
)

# CSRF trusted origins (مهم عند استخدام HTTPS والدومينات)
# مثال:
# DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# إن كنت خلف Proxy / Load Balancer (مثل Nginx) وتريد احترام X-Forwarded-Proto
# DJANGO_SECURE_PROXY_SSL_HEADER=true
if env_bool("DJANGO_SECURE_PROXY_SSL_HEADER", False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# =========================
# تعريف التطبيقات
# =========================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # THQAF apps (الأساسية كبداية)
    "accounts",
    "organizations",
    "individuals",

    # Pages (Landing + Public pages)
    "pages",
]

AUTH_USER_MODEL = "accounts.User"


# =========================
# الوسطاء (Middleware)
# LocaleMiddleware مهم للغة/التعريب
# =========================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # مهم للتعريب
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "thqaf.urls"


# =========================
# القوالب (Templates)
# =========================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # مجلد قوالب عام
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


WSGI_APPLICATION = "thqaf.wsgi.application"


# =========================
# قاعدة البيانات
# افتراضيًا SQLite، ويمكن التبديل عبر متغيرات بيئة (PostgreSQL مثلاً)
# =========================
DB_ENGINE = env("DB_ENGINE", "sqlite")

if DB_ENGINE == "postgres":
    # مثال متغيرات:
    # DB_ENGINE=postgres
    # DB_NAME=thqaf_db
    # DB_USER=thqaf_user
    # DB_PASSWORD=...
    # DB_HOST=127.0.0.1
    # DB_PORT=5432
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", "thqaf_db"),
            "USER": env("DB_USER", "postgres"),
            "PASSWORD": env("DB_PASSWORD", ""),
            "HOST": env("DB_HOST", "127.0.0.1"),
            "PORT": env("DB_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        }
    }
else:
    # SQLite (مناسب للتطوير/التجربة)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# =========================
# تحقق كلمات المرور
# =========================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# =========================
# الدولية والتعريب
# =========================
LANGUAGE_CODE = "ar"

LANGUAGES = [
    ("ar", "العربية"),
    ("en", "English"),
]

TIME_ZONE = "Asia/Riyadh"

USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / "locale",
]


# =========================
# الملفات الثابتة والوسائط
# =========================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # للإنتاج (collectstatic)

# للتطوير: هذا مهم عشان يقرأ static من مشروعك
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# إعدادات افتراضية
# =========================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================
# جلسات + Cookies (تحسينات أمان)
# =========================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # يفضل تركها False غالبًا (Django default)
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"


# =========================
# البريد الإلكتروني (OTP) - اختياري لاحقًا
# =========================
# مثال:
# EMAIL_BACKEND=smtp
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_HOST_USER=...
# EMAIL_HOST_PASSWORD=...
# EMAIL_USE_TLS=true
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend" if DEBUG else "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = env("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "THQAF <no-reply@thqaf.local>")


# =========================
# إعدادات أمان إضافية للإنتاج
# =========================
# عند DEBUG=False ننصح بتفعيل التالي عبر متغيرات بيئة:
# DJANGO_SECURE=true
if env_bool("DJANGO_SECURE", False) and not DEBUG:
    SECURE_SSL_REDIRECT = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"


# =========================
# Logging (لتتبع الأخطاء)
# =========================
LOG_LEVEL = env("DJANGO_LOG_LEVEL", "INFO")

# تأكد أن مجلد logs موجود
(LOGS_DIR := BASE_DIR / "logs").mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple" if DEBUG else "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "django.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"] + ([] if DEBUG else ["file"]),
            "level": LOG_LEVEL,
            "propagate": True,
        },
    },
}
