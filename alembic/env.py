from alembic import context
from app.config import settings
from app.database import Base, engine
from app import models  # noqa
context.configure  # keep import
def run():
    with engine.connect() as conn:
        context.configure(connection=conn, target_metadata=Base.metadata)
        with context.begin_transaction(): context.run_migrations()
run()
