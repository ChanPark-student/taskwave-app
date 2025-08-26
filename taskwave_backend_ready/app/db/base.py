from sqlalchemy.orm import declarative_base
Base = declarative_base()
from app.models import user, subject, schedule, material, upload  # noqa
