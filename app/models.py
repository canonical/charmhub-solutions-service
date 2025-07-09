from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer,
    String,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app import db


class Solution(db.Model):
    __tablename__ = "solution"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True
    )  # unique ID because we will publish multiple versions of the same solution
    solution_name: Mapped[str] = mapped_column(String, nullable=False)  # slug
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    short_description: Mapped[Optional[str]] = mapped_column(
        Text
    )  # markdown allowed
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

    publisher_id: Mapped[str] = mapped_column(
        ForeignKey("publisher.publisher_id"), nullable=False
    )
    publisher: Mapped["Publisher"] = relationship(backref="solutions")

    use_cases: Mapped[Optional[List["UseCase"]]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )
    deployable_on: Mapped["DeployableOn"] = relationship(
        back_populates="solution", cascade="all, delete-orphan", uselist=False
    )
    documentation: Mapped[Optional["Documentation"]] = relationship(
        back_populates="solution", cascade="all, delete-orphan", uselist=False
    )
    charms: Mapped[List["Charm"]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )
    compatibility: Mapped[Optional["Compatibility"]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
    )  # juju versions compatibility
    maintainers: Mapped[Optional[List["Maintainer"]]] = relationship(
        back_populates="solution", cascade="all, delete-orphan"
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


class DeployableOn(db.Model):
    __tablename__ = "deployable_on"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(
        String, nullable=False
    )  # kubernetes or machine
    version: Mapped[Optional[List[str]]] = mapped_column(
        JSON
    )  # list of platform version constraints
    prerequisites: Mapped[Optional[List[str]]] = mapped_column(
        JSON
    )  # list of platform prerequisites
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="deployable_on")


class Documentation(db.Model):
    __tablename__ = "documentation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    main: Mapped[Optional[str]] = mapped_column(String)
    source: Mapped[Optional[str]] = mapped_column(String)  # github source repo
    get_started: Mapped[Optional[str]] = mapped_column(String)
    how_to_operate: Mapped[Optional[str]] = mapped_column(String)
    architecture_diagram: Mapped[Optional[str]] = mapped_column(
        String
    )  # URL to architecture diagram
    architecture_explanation: Mapped[Optional[str]] = mapped_column(
        Text
    )  # markdown allowed
    submit_a_bug: Mapped[Optional[str]] = mapped_column(String)
    community_discussion: Mapped[Optional[str]] = mapped_column(String)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="documentation")


class Charm(db.Model):
    __tablename__ = "charm"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    charm_name: Mapped[str] = mapped_column(String, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="charms")


class Compatibility(db.Model):
    __tablename__ = "compatibility"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    juju_versions: Mapped[Optional[List[str]]] = mapped_column(JSON)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="compatibility")


class Maintainer(db.Model):
    __tablename__ = "maintainer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="maintainers")


class UsefulLink(db.Model):
    __tablename__ = "useful_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="useful_links")
