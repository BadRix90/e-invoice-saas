"""
Django Settings Module

Usage:
    - Development: DJANGO_SETTINGS_MODULE=config.settings.dev
    - Production: DJANGO_SETTINGS_MODULE=config.settings.prod

Default: Development settings
"""

import os

environment = os.getenv("DJANGO_ENV", "dev")

if environment == "prod":
    from .prod import *  # noqa: F401, F403
else:
    from .dev import *  # noqa: F401, F403
