"""
Repository implementation for vmail.
"""

import time
import typing

import sqlalchemy
import sqlalchemy.orm
import sqlalchemy.exc
from . import hash_something
from . import model
from .db import Email


class BaseRepo:
    def __init__(self, session: sqlalchemy.orm.Session):
        self._session = session

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        if any([exc_type, exc_value, exc_traceback]):
            self._session.rollback()
            return
        try:
            self._session.commit()
        except sqlalchemy.exc.DatabaseError as e:
            self._session.rollback()
            raise e


class VmailRepo(BaseRepo):
    def clear(self) -> int:
        try:
            n_deleted = self._session.query(Email).delete()
            self._session.commit()
            return n_deleted
        except Exception as e:
            self._session.rollback()
            raise e

    def save(self, email_address: str):
        hashed = hash_something(email_address)
        self._session.add(Email(address=hashed))
        try:
            self._session.commit()
        except sqlalchemy.exc.DatabaseError as e:
            self._session.rollback()
            raise e

    def get_instance(self, email_address: str) -> typing.Optional[Email]:
        key = hash_something(email_address)
        instance = self._session.query(Email).filter(Email.address == key).first()
        if not instance:
            return None
        return instance

    def get_instance_by_token(self, token: str) -> typing.Optional[Email]:
        instance = self._session.query(Email).filter(Email.token == token).first()
        if instance is None:
            return None
        return instance

    @classmethod
    def _is_verified(cls, email: Email) -> model.VerifiedEnum:
        if email is None:
            return model.VerifiedEnum.unverified
        if email.trequested is None:
            return model.VerifiedEnum.unverified
        if email.tverified is None:
            return model.VerifiedEnum.unverified
        if email.tverified < email.trequested:
            return model.VerifiedEnum.expired
        if email.token is not None:
            return model.VerifiedEnum.pending
        return model.VerifiedEnum.verified

    def read(self, email_address: str) -> typing.Optional[model.EmailAddress]:
        instance = self.get_instance(email_address)
        if instance is None:
            return None
        verified = VmailRepo._is_verified(instance)
        return model.EmailAddress(address=email_address, verified=verified)

    def verification_requested(self, email_address: str, token: str) -> typing.Optional[float]:
        """
        Sets the OTP token for the specified email address

        Args:
            email: Email address
            token: OTP token

        Returns:
            Float indicating the timestamp of the verification process,
            or None if email is not found.

        """
        test = self.get_instance_by_token(token)
        if test is not None:
            raise ValueError("Token already in use.")
        instance = self.get_instance(email_address)
        if instance is None:
            return None
        instance.token = token
        instance.trequested = time.time()
        self._session.commit()
        return instance.trequested

    def verify(self, token: str, expiration_seconds: float = 3600) -> model.VerifiedEnum:
        """
        Check the provided token matches one recently issued
        and that it was received within the expiration time.

        Args:
            email: Email address
            token: Previously issued token

        Returns:
            True if the token matches and is valid.

        """
        instance = self.get_instance_by_token(token)
        if instance is None:
            return model.VerifiedEnum.unverified
        if instance.trequested is None:
            return model.VerifiedEnum.unverified
        tverified = time.time()
        if tverified - instance.trequested > expiration_seconds:
            return model.VerifiedEnum.expired
        instance.tverified = tverified
        instance.token = None
        self._session.commit()
        return model.VerifiedEnum.verified
