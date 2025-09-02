"""Aerich configuration for database migrations"""

from app.config.db import TortoiseSettings

# Get the Tortoise settings
tortoise_settings = TortoiseSettings.generate()

TORTOISE_ORM = {
    "connections": {"default": tortoise_settings.db_url},
    "apps": {
        "models": {
            "models": tortoise_settings.modules["models"] + ["aerich.models"],
            "default_connection": "default",
        },
    },
}