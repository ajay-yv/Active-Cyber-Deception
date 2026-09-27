from sqlalchemy.orm import DeclarativeBase


class RealBase(DeclarativeBase):
    pass


class SyntheticBase(DeclarativeBase):
    pass


class SecurityBase(DeclarativeBase):
    pass


# Backward-compatible alias for modules that still import Base during the transition.
Base = RealBase
