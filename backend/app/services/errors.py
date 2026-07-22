class ServiceError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class InviteInvalidError(ServiceError):
    pass


class UserAlreadyExistsError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass
