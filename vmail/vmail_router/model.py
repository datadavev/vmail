"""
Data model for vmail API
"""

import enum
import typing
import pydantic


class VerifiedEnum(enum.IntEnum):
    # Email has not been verified
    unverified = 0
    # Email has been verified
    verified = 1
    # Email verification is awaiting a response from the subject
    pending = 2
    # The email verification has expired
    expired = 3


class EmailAddress(pydantic.BaseModel):
    address: str
    normalized: typing.Optional[str] = None
    verified: VerifiedEnum = VerifiedEnum.unverified
    valid: bool = False
    message: typing.Optional[str] = None

class VerifiedResponse(pydantic.BaseModel):
    verified: bool
    state: VerifiedEnum
