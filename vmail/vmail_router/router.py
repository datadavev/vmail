"""
FastAPI router implementing the vmail endpoints.

"""

import logging
import typing
import email_validator
import fastapi
import sqlalchemy.exc

from . import create_otp, send_verification_email
from . import model

L = logging.getLogger("vmail.router")


def get_vmail_router(
    get_settings: typing.Callable,
    dependencies: typing.List[fastapi.Depends] = None,
) -> fastapi.APIRouter:
    settings = get_settings()
    router = fastapi.APIRouter(dependencies=dependencies)

    def get_verify_url(token: str) -> str:
        url = settings.verify_url
        return url.format(token=token)

    @router.get("/valid")
    async def test_email_valid(
        email: str, request: fastapi.Request
    ) -> model.EmailAddress:
        """
        Checks validity of an email address.
        """
        result = model.EmailAddress(address=email)
        try:
            emailinfo = email_validator.validate_email(email, check_deliverability=True)
            result.normalized = emailinfo.normalized
            result.valid = True
            result.verified = False
            result.message = "OK"
        except email_validator.EmailNotValidError as e:
            result.valid = False
            result.verified = False
            result.message = str(e)
        return result

    @router.post("/register")
    async def register_email_post(
        request: fastapi.Request,
        email: typing.Annotated[str, fastapi.Form()],
        name: typing.Annotated[typing.Optional[str], fastapi.Form()] = None,
        appname: typing.Annotated[typing.Optional[str], fastapi.Form()] = None,
    ) -> model.EmailAddress:
        """
        Generates an OTP and sends it via email to the provided address.

        The recipient must visit the included URL to verify the email.

        Args:
            email:
            token:

        Returns:

        """
        result = model.EmailAddress(address=email)
        try:
            emailinfo = email_validator.validate_email(
                email, check_deliverability=False
            )
            result.normalized = emailinfo.normalized
            result.valid = True
            result.verified = model.VerifiedEnum.unverified
            result.message = "OK"
            # Is email already verified?
            verified_email = request.state.vmailrepo.read(emailinfo.normalized)
            if verified_email is not None:
                if verified_email.verified == model.VerifiedEnum.verified:
                    result.verified = verified_email.verified
                    return result
            email_token = create_otp()
            verify_url = get_verify_url(email_token)
            try:
                request.state.vmailrepo.save(emailinfo.normalized)
            except sqlalchemy.exc.IntegrityError:
                L.warning("Email already registered")
            send_result = await send_verification_email(
                email=emailinfo.normalized,
                otp=email_token,
                verify_url=verify_url,
                name=name,
                app_name=appname,
            )
            if send_result:
                request.state.vmailrepo.verification_requested(
                    emailinfo.normalized, email_token
                )
                result.verified = model.VerifiedEnum.pending
                result.message = "Verification request sent"
            else:
                result.message = "There was an error sending the verification request"
        except email_validator.EmailNotValidError as e:
            result.valid = False
            result.verified = model.VerifiedEnum.unverified
            result.message = str(e)
        return result

    @router.get("/verified")
    async def email_verification_status(
        email: str, request: fastapi.Request
    ) -> model.EmailAddress:
        """
        Given an email address, return its verification status.

        Args:
            email: The email address
            request: The fastapi request

        Returns:

        """
        result = model.EmailAddress(address=email)
        try:
            emailinfo = email_validator.validate_email(
                email, check_deliverability=False
            )
            result.normalized = emailinfo.normalized
            result.valid = True
        except email_validator.EmailNotValidError as e:
            result.valid = False
            result.verified = model.VerifiedEnum.unverified
            result.message = str(e)
            return result
        record = request.state.vmailrepo.read(result.normalized)
        if record is not None:
            result.verified = record.verified
            result.message = "OK"
        else:
            result.verified = model.VerifiedEnum.unverified
            result.message = "Address is valid but not verified"
        return result

    @router.get("/verify/{token}")
    async def verify_email(
        token: typing.Annotated[
            str,
            fastapi.Path(
                title="OTP value",
                max_length=settings.otp_digits,
                min_length=settings.otp_digits,
            ),
        ],
        request: fastapi.Request,
    ) -> model.VerifiedResponse:
        """
        Given a previously sent OTP code, update the email with its verification status.

        Args:
            token:
            request:

        Returns:

        """
        # TODO: Check token is not expired (too old)
        entry = request.state.vmailrepo.get_instance_by_token(token)
        if entry is None:
            raise fastapi.HTTPException(status_code=404)
        state = request.state.vmailrepo.verify(token)
        return model.VerifiedResponse(
            verified=state, state=state == model.VerifiedEnum.verified
        )

    return router
