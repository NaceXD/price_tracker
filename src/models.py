from datetime import datetime
from sqlalchemy import ForeignKey, Table, Column, Integer, String, func, DateTime, Boolean
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


user_tracked_routes = Table(
    "user_tracked_routes",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("route_id", ForeignKey("tracked_routes.id", ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    profile: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    routes: Mapped[list["TrackedRoute"]] = relationship(
        "TrackedRoute",
        secondary=user_tracked_routes,
        back_populates="users",
    )


class Profile(Base):
    __tablename__ = 'profiles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    telegram_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    send_email: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")

class TrackedRoute(Base):
    __tablename__ = 'tracked_routes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    origin: Mapped[str] = mapped_column(String(10), nullable=False)
    destination: Mapped[str] = mapped_column(String(10), nullable=False)
    departure_data: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    users: Mapped[list["User"]] = relationship(
        "User",
        secondary=user_tracked_routes,
        back_populates="routes"
    )

    price_history: Mapped[list["PriceHistory"]] = relationship(
        "PriceHistory",
        back_populates="route",
        cascade="all, delete-orphan"
    )


class PriceHistory(Base):
    __tablename__ = 'price_history'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("tracked_routes.id", ondelete="CASCADE"))
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    route: Mapped["TrackedRoute"] = relationship("TrackedRoute", back_populates="price_history")