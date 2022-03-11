class SubjAPIError(Exception):
    pass


class NoCredentialsError(SubjAPIError):
    pass


class IncorrectPasswordError(SubjAPIError):
    pass


class NotConnectedError(SubjAPIError):
    pass
