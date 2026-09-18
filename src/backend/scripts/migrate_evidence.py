import os
import sys

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
from app.models import Evidence


def migrate():
    print()
    print("Creating evidence table...")
    print()

    Evidence.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    print("Evidence table ready.")
    print()


if __name__ == "__main__":
    migrate()