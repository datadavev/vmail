"""
Data model for vmail API
"""

import enum
import typing
import pydantic


class VerifiedEnum(enum.IntEnum):
    unverified = 0
    verified = 1
    pending = 2
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
