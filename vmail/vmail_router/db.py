"""
Database definition for vmail application
"""
import time

import sqlalchemy.orm

SQL_BASE = sqlalchemy.orm.declarative_base()

class Email(SQL_BASE):
    """
    Implements SQLAlchemy ORM for storing hashed email addresses for verification.
    """

    __tablename__ = "email"

    address: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        doc="Hash of email address", primary_key=True
    )

    token: sqlalchemy.orm.Mapped[str] = sqlalchemy.orm.mapped_column(
        doc="One time passcode for user validation of email address",
        nullable=True,
        default=None,
    )

    tcreated: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.types.Float, doc="Time when entry was created", default=time.time
    )

    trequested: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.types.Float,
        doc="Time when a request to verify was sent, NULL if unsent",
        nullable=True,
        default=None,
    )

    tverified: sqlalchemy.orm.Mapped[float] = sqlalchemy.orm.mapped_column(
        sqlalchemy.types.Float,
        doc="Time when entry was verified or NULL for unverified",
        nullable=True,
        default=None,
    )
