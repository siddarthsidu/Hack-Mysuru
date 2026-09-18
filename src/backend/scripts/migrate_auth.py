import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    ),
)

from app.database import Base, engine
from app.models import Notification


def migrate():
    print("\nStarting CivicRoute authentication migration...\n")

    inspector = inspect(engine)

    # -----------------------------------------------------
    # Add user_id to complaints
    # -----------------------------------------------------

    complaint_columns = {
        column["name"]
        for column in inspector.get_columns("complaints")
    }

    if "user_id" not in complaint_columns:

        print("Adding complaints.user_id...")

        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    ALTER TABLE complaints
                    ADD COLUMN user_id INTEGER
                    """
                )
            )

            connection.execute(
                text(
                    """
                    ALTER TABLE complaints
                    ADD CONSTRAINT fk_complaints_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    """
                )
            )

            connection.execute(
                text(
                    """
                    CREATE INDEX ix_complaints_user_id
                    ON complaints(user_id)
                    """
                )
            )

        print("complaints.user_id added.")

    else:
        print("complaints.user_id already exists.")

    # -----------------------------------------------------
    # Create notifications table
    # -----------------------------------------------------

    if "notifications" not in inspector.get_table_names():

        print("Creating notifications table...")

        Base.metadata.create_all(
            bind=engine,
            tables=[Notification.__table__],
        )

        print("notifications table created.")

    else:
        print("notifications table already exists.")

    print("\nMigration completed successfully.\n")


if __name__ == "__main__":
    migrate()