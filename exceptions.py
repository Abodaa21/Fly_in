
class InvalidLine(Exception):
    """Raised when a line in the configuration file fails validation.

    Carries a human-readable message describing the offending line number
    and the expected format.
    """
    pass
