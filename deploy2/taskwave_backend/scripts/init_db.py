from app.db.session import engine
from app.db.base import Base
from app.models import user, subject, schedule, material, upload  # noqa

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done.")
