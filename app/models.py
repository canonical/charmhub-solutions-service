from datetime import datetime
import enum
from typing import Optional, List
from sqlalchemy import (
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Enum,
    Table,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app import db


class SolutionStatus(enum.Enum):
    PENDING = "pending"  # publisher registers name, reviewer hasn't approved
    UNPUBLISHED = "unpublished"  # reviewer approved but metadata not submitted
    PENDING_REVIEW = "pending_review"  # metadata submitted for review
    PUBLISHED = "published"  # solution publicly visible


class PlatformTypes(enum.Enum):
    KUBERNETES = "kubernetes"
    MACHINE = "machine"


# Association table for many-to-many between Solution and Maintainer
solution_maintainer = Table(
    "solution_maintainer",
    db.Model.metadata,
    db.Column("solution_id", ForeignKey("solution.id"), primary_key=True),
    db.Column("maintainer_id", ForeignKey("maintainer.id"), primary_key=True),
)


class Solution(db.Model):
    __tablename__ = "solution"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )  # unique ID because we will publish multiple versions of the same solution
    solution_name: Mapped[str] = mapped_column(String, nullable=False)  # slug
    display_name: Mapped[str] = mapped_column(
        String, nullable=False
    )  # title case name of soltuion
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(
        String
    )  # no markdown allowed
    long_description: Mapped[Optional[str]] = mapped_column(
        Text
    )  # markdown allowed
    terraform_modules: Mapped[Optional[str]] = mapped_column(
        String
    )  # URL to terraform modules
    icon: Mapped[Optional[str]] = mapped_column(String)  # URL to icon
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # solution status
    status: Mapped[SolutionStatus] = mapped_column(
        Enum(SolutionStatus), nullable=False, default=SolutionStatus.PENDING
    )

    # platform: "kubernetes" or "machine"
    platform: Mapped[PlatformTypes] = mapped_column(
        Enum(PlatformTypes), nullable=False
    )
    platform_version: Mapped[Optional[List[str]]] = mapped_column(
        JSON
    )  # list of platform version constraints
    platform_prerequisites: Mapped[Optional[List[str]]] = mapped_column(
        JSON
    )  # list of platform prerequisites

    # documentation links
    documentation_main: Mapped[Optional[str]] = mapped_column(String)
    documentation_source: Mapped[Optional[str]] = mapped_column(
        String
    )  # github source repo
    get_started_url: Mapped[Optional[str]] = mapped_column(String)
    how_to_operate_url: Mapped[Optional[str]] = mapped_column(String)
    architecture_diagram_url: Mapped[Optional[str]] = mapped_column(String)
    architecture_explanation: Mapped[Optional[str]] = mapped_column(Text)
    submit_bug_url: Mapped[Optional[str]] = mapped_column(String)
    community_discussion_url: Mapped[Optional[str]] = mapped_column(String)

    # compatibility with juju versions
    juju_versions: Mapped[Optional[List[str]]] = mapped_column(JSON)

    publisher_id: Mapped[str] = mapped_column(
        ForeignKey("publisher.publisher_id"), nullable=False
    )
    publisher: Mapped["Publisher"] = relationship(backref="solutions")

    use_cases: Mapped[Optional[List["UseCase"]]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )
    charms: Mapped[List["Charm"]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )
    maintainers: Mapped[List["Maintainer"]] = relationship(
        secondary=solution_maintainer, back_populates="solutions"
    )
    useful_links: Mapped[Optional[List["UsefulLink"]]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "solution_name", "version", name="_solution_version_uc"
        ),
    )


class Publisher(db.Model):
    __tablename__ = "publisher"

    publisher_id: Mapped[str] = mapped_column(
        String, primary_key=True
    )  # publisher_id we get from the storeAPI (Launchpad group)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)


class UseCase(db.Model):
    __tablename__ = "use_case"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="use_cases")


class Charm(db.Model):
    __tablename__ = "charm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    charm_name: Mapped[str] = mapped_column(
        String, nullable=False
    )  # charm slug
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="charms")

    __table_args__ = (
        UniqueConstraint(
            "solution_id", "charm_name", name="_solution_charm_uc"
        ),
    )


class Maintainer(db.Model):
    __tablename__ = "maintainer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    solutions: Mapped[List["Solution"]] = relationship(
        secondary=solution_maintainer, back_populates="maintainers"
    )


class UsefulLink(db.Model):
    __tablename__ = "useful_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="useful_links")
