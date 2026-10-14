"""Relational database models for SportBot using SQLAlchemy 2.0."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base declarative class for all database models."""
    pass


class User(Base):
    """Athlete user entity tracked across 30-day training cycles."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_day: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    current_cycle: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    difficulty_mode: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    workout_logs: Mapped[List["WorkoutLog"]] = relationship(
        "WorkoutLog", back_populates="user", cascade="all, delete-orphan"
    )
    weight_logs: Mapped[List["WeightLog"]] = relationship(
        "WeightLog", back_populates="user", cascade="all, delete-orphan"
    )


class Exercise(Base):
    """Calisthenics bodyweight exercise catalog."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # push, pull, legs, core, cardio
    metric_type: Mapped[str] = mapped_column(String(16), nullable=False)  # reps, seconds, minutes
    description: Mapped[str] = mapped_column(Text, nullable=False)
    technique_tips: Mapped[str] = mapped_column(Text, nullable=False)

    progressions: Mapped[List["ExerciseProgression"]] = relationship(
        "ExerciseProgression", back_populates="exercise", cascade="all, delete-orphan"
    )
    cycle_day_associations: Mapped[List["CycleDayExercise"]] = relationship(
        "CycleDayExercise", back_populates="exercise", cascade="all, delete-orphan"
    )


class ExerciseProgression(Base):
    """Exercise progression tiers (light, medium, hard) for calisthenics scaling."""

    __tablename__ = "exercise_progressions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    difficulty_tier: Mapped[str] = mapped_column(String(16), nullable=False)  # light, medium, hard
    progression_name: Mapped[str] = mapped_column(String(128), nullable=False)
    target_sets: Mapped[int] = mapped_column(Integer, nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    tempo: Mapped[str] = mapped_column(String(16), default="3-1-1", nullable=False)
    rest_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="progressions")


class CycleDay(Base):
    """Specific day in the 30-day training cycle."""

    __tablename__ = "cycle_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_number: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    block_type: Mapped[str] = mapped_column(String(32), nullable=False)  # A_PUSH, B_PULL, C_LEGS_RUN, REST
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    focus_areas: Mapped[str] = mapped_column(String(128), nullable=False)
    is_rest_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    exercises: Mapped[List["CycleDayExercise"]] = relationship(
        "CycleDayExercise", back_populates="cycle_day", cascade="all, delete-orphan", order_by="CycleDayExercise.order"
    )


class CycleDayExercise(Base):
    """Ordered mapping of exercises assigned to a cycle day."""

    __tablename__ = "cycle_day_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cycle_day_id: Mapped[int] = mapped_column(Integer, ForeignKey("cycle_days.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    cycle_day: Mapped["CycleDay"] = relationship("CycleDay", back_populates="exercises")
    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="cycle_day_associations")


class WorkoutLog(Base):
    """Completed workout session logging."""

    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="workout_logs")
    exercise_logs: Mapped[List["WorkoutExerciseLog"]] = relationship(
        "WorkoutExerciseLog", back_populates="workout_log", cascade="all, delete-orphan"
    )


class WorkoutExerciseLog(Base):
    """Specific exercise performance record within a workout session."""

    __tablename__ = "workout_exercise_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workout_log_id: Mapped[int] = mapped_column(Integer, ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id"), nullable=False)
    sets_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    value_completed: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workout_log: Mapped["WorkoutLog"] = relationship("WorkoutLog", back_populates="exercise_logs")
    exercise: Mapped["Exercise"] = relationship("Exercise")


class WeightLog(Base):
    """Periodic bodyweight check-in for progressive athletic adaptation tracking."""

    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="weight_logs")
