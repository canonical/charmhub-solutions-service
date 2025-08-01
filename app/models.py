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
from app.extensions import db


class SolutionStatus(enum.Enum):
    PENDING_NAME_REVIEW = (
        "pending_name_review"  # publisher requests new solution
    )
    PENDING_METADATA_SUBMISSION = "pending_metadata_submission"  # empty solution created, metadata not yet submitted
    PENDING_METADATA_REVIEW = (
        "pending_metadata_review"  # metadata submitted for review
    )
    PUBLISHED = "published"  # solution publicly visible
    DRAFT = "draft"  # on publisher edit page, if publisher clicks "save" to preview solution


class PlatformTypes(enum.Enum):
    KUBERNETES = "kubernetes"
    MACHINE = "machine"


# private solutions are only visible to the publisher and maintainers
class Visibility(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class ReviewerActionType(enum.Enum):
    APPROVE_REGISTRATION = "approve_registration"
    PUBLISH = "publish"
    UNPUBLISH = "unpublish"


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
    )  # unique ID because we will publish multiple revisions of the same solution
    hash: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # slug
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Launchpad username
    title: Mapped[str] = mapped_column(
        String, nullable=False
    )  # title case name of soltuion
    summary: Mapped[Optional[str]] = mapped_column(
        String
    )  # no markdown allowed
    description: Mapped[Optional[str]] = mapped_column(
        Text
    )  # markdown allowed
    terraform_modules: Mapped[Optional[str]] = mapped_column(
        String
    )  # URL to terraform modules
    icon: Mapped[Optional[str]] = mapped_column(String)  # URL to icon
    created: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # solution status
    status: Mapped[SolutionStatus] = mapped_column(
        Enum(SolutionStatus),
        nullable=False,
        default=SolutionStatus.PENDING_NAME_REVIEW,
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
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility), nullable=False, default=Visibility.PUBLIC
    )

    __table_args__ = (
        UniqueConstraint("name", "revision", name="_solution_revision_uc"),
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

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
        }


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

    def to_dict(self):
        return {
            "id": self.id,
            "charm_name": self.charm_name,
        }


"""
A Maintainer will be a manually entered field by the publisher,
and will determine the point(s) of contact for the solution.
All members of the Launchpad group will still be able to edit the solution
even if they are not listed as Maintainers.
"""


class Maintainer(db.Model):
    __tablename__ = "maintainer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)

    solutions: Mapped[List["Solution"]] = relationship(
        secondary=solution_maintainer, back_populates="maintainers"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
            "email": self.email,
        }


class UsefulLink(db.Model):
    __tablename__ = "useful_link"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )

    solution: Mapped["Solution"] = relationship(back_populates="useful_links")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
        }


class ReviewAction(db.Model):
    __tablename__ = "review_action"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    solution_id: Mapped[int] = mapped_column(
        ForeignKey("solution.id"), nullable=False
    )
    reviewer_id: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Launchpad username
    action: Mapped[ReviewerActionType] = mapped_column(
        Enum(ReviewerActionType), nullable=False
    )
    comment: Mapped[Optional[str]] = mapped_column(Text)  # optional comment
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    solution: Mapped["Solution"] = relationship(backref="review_actions")
