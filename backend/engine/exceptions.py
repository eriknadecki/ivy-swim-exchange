class EngineError(Exception):
    """Base class for errors raised by the matching engine."""


class InvalidOrderError(EngineError):
    pass


class UnknownMarketError(EngineError):
    pass
