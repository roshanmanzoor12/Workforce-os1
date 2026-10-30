from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.tenant_base import (
    TenantBase,
    TenantStandardModelMixin,
)


# =========================================================
# EMPLOYMENT STATUS
# =========================================================

EMPLOYMENT_STATUS_ACTIVE = "active"
EMPLOYMENT_STATUS_ON_LEAVE = "on_leave"
EMPLOYMENT_STATUS_SUSPENDED = "suspended"
EMPLOYMENT_STATUS_TERMINATED = "terminated"

EMPLOYMENT_STATUSES = (
    EMPLOYMENT_STATUS_ACTIVE,
    EMPLOYMENT_STATUS_ON_LEAVE,
    EMPLOYMENT_STATUS_SUSPENDED,
    EMPLOYMENT_STATUS_TERMINATED,
)


# =========================================================
# DEPARTMENT
# =========================================================


class Department(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Organizational department inside exactly one tenant database.

    Examples:

        Engineering
        Finance
        Human Resources
        Customer Support

    No workspace_id column is required because physical database
    isolation already scopes this record to one workspace.
    """

    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="uq_departments_name",
        ),
        UniqueConstraint(
            "code",
            name="uq_departments_code",
        ),
        Index(
            "ix_departments_is_active",
            "is_active",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    teams: Mapped[list["Team"]] = relationship(
        back_populates="department",
        passive_deletes=True,
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="department",
        foreign_keys="Employee.department_id",
        passive_deletes=True,
    )


# =========================================================
# TEAM
# =========================================================


class Team(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Team inside a department.

    A team may exist without a department so smaller workspaces do
    not need to create unnecessary hierarchy.
    """

    __tablename__ = "teams"

    __table_args__ = (
        UniqueConstraint(
            "name",
            "department_id",
            name="uq_teams_name_department_id",
        ),
        UniqueConstraint(
            "code",
            name="uq_teams_code",
        ),
        Index(
            "ix_teams_department_id",
            "department_id",
        ),
        Index(
            "ix_teams_is_active",
            "is_active",
        ),
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    department_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "departments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    department: Mapped[
        Department | None
    ] = relationship(
        back_populates="teams",
    )

    employees: Mapped[list["Employee"]] = relationship(
        back_populates="team",
        foreign_keys="Employee.team_id",
        passive_deletes=True,
    )


# =========================================================
# EMPLOYEE
# =========================================================


class Employee(
    TenantStandardModelMixin,
    TenantBase,
):
    """
    Workforce record inside one tenant.

    Employee is intentionally separate from the global User model.

    user_id:

        optional UUID reference to a global control-plane user

    Important:

        user_id is NOT a database ForeignKey because PostgreSQL
        cannot enforce a normal foreign key across separate tenant
        and control databases.

    An employee may therefore exist before a login account is
    created or linked.
    """

    __tablename__ = "employees"

    __table_args__ = (
        UniqueConstraint(
            "employee_code",
            name="uq_employees_employee_code",
        ),
        UniqueConstraint(
            "work_email",
            name="uq_employees_work_email",
        ),
        UniqueConstraint(
            "user_id",
            name="uq_employees_user_id",
        ),
        CheckConstraint(
            (
                "employment_status IN "
                "('active', 'on_leave', 'suspended', 'terminated')"
            ),
            name="ck_employees_employment_status",
        ),
        CheckConstraint(
            (
                "termination_date IS NULL "
                "OR hire_date IS NULL "
                "OR termination_date >= hire_date"
            ),
            name="ck_employees_termination_after_hire",
        ),
        CheckConstraint(
            "manager_id IS NULL OR manager_id <> id",
            name="ck_employees_manager_not_self",
        ),
        Index(
            "ix_employees_department_id",
            "department_id",
        ),
        Index(
            "ix_employees_team_id",
            "team_id",
        ),
        Index(
            "ix_employees_manager_id",
            "manager_id",
        ),
        Index(
            "ix_employees_employment_status",
            "employment_status",
        ),
        Index(
            "ix_employees_is_active",
            "is_active",
        ),
        Index(
            "ix_employees_first_name_last_name",
            "first_name",
            "last_name",
        ),
    )

    # -----------------------------------------------------
    # GLOBAL USER LINK
    # -----------------------------------------------------

    user_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # -----------------------------------------------------
    # INTERNAL IDENTITY
    # -----------------------------------------------------

    employee_code: Mapped[
        str
    ] = mapped_column(
        String(50),
        nullable=False,
    )

    # -----------------------------------------------------
    # PERSONAL / WORK IDENTITY
    # -----------------------------------------------------

    first_name: Mapped[
        str
    ] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[
        str
    ] = mapped_column(
        String(100),
        nullable=False,
    )

    work_email: Mapped[
        str | None
    ] = mapped_column(
        String(320),
        nullable=True,
    )

    phone_number: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
    )

    avatar_url: Mapped[
        str | None
    ] = mapped_column(
        String(2048),
        nullable=True,
    )

    # -----------------------------------------------------
    # EMPLOYMENT
    # -----------------------------------------------------

    job_title: Mapped[
        str | None
    ] = mapped_column(
        String(150),
        nullable=True,
    )

    employment_status: Mapped[
        str
    ] = mapped_column(
        String(30),
        nullable=False,
        default=EMPLOYMENT_STATUS_ACTIVE,
    )

    hire_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    termination_date: Mapped[
        date | None
    ] = mapped_column(
        Date,
        nullable=True,
    )

    is_active: Mapped[
        bool
    ] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # -----------------------------------------------------
    # ORGANIZATION STRUCTURE
    # -----------------------------------------------------

    department_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "departments.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    team_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "teams.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    manager_id: Mapped[
        uuid.UUID | None
    ] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # -----------------------------------------------------
    # RELATIONSHIPS
    # -----------------------------------------------------

    department: Mapped[
        Department | None
    ] = relationship(
        back_populates="employees",
        foreign_keys=[
            department_id
        ],
    )

    team: Mapped[
        Team | None
    ] = relationship(
        back_populates="employees",
        foreign_keys=[
            team_id
        ],
    )

    manager: Mapped[
        "Employee | None"
    ] = relationship(
        remote_side="Employee.id",
        foreign_keys=[
            manager_id
        ],
        back_populates="direct_reports",
    )

    direct_reports: Mapped[
        list["Employee"]
    ] = relationship(
        back_populates="manager",
        foreign_keys=[
            manager_id
        ],
        passive_deletes=True,
    )

    # -----------------------------------------------------
    # DISPLAY NAME
    # -----------------------------------------------------

    @property
    def full_name(
        self,
    ) -> str:
        return (
            f"{self.first_name} "
            f"{self.last_name}"
        ).strip()


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "EMPLOYMENT_STATUS_ACTIVE",
    "EMPLOYMENT_STATUS_ON_LEAVE",
    "EMPLOYMENT_STATUS_SUSPENDED",
    "EMPLOYMENT_STATUS_TERMINATED",
    "EMPLOYMENT_STATUSES",
    "Department",
    "Team",
    "Employee",
]