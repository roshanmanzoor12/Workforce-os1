from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictError,
    ResourceNotFound,
    ValidationError,
)
from app.modules.employees.models import (
    EMPLOYMENT_STATUS_ACTIVE,
    EMPLOYMENT_STATUS_TERMINATED,
    Department,
    Employee,
    Team,
)
from app.modules.employees.repository import EmployeeRepository
from app.modules.employees.schemas import (
    DepartmentCreateRequest,
    DepartmentDeleteResponse,
    DepartmentListResponse,
    DepartmentPublic,
    DepartmentResponse,
    DepartmentUpdateRequest,
    EmployeeCreateRequest,
    EmployeeDeleteResponse,
    EmployeeDetailResponse,
    EmployeeListResponse,
    EmployeePublic,
    EmployeeResponse,
    EmployeeUpdateRequest,
    TeamCreateRequest,
    TeamDeleteResponse,
    TeamListResponse,
    TeamPublic,
    TeamResponse,
    TeamUpdateRequest,
)


# =========================================================
# EMPLOYEE SERVICE
# =========================================================


class EmployeeService:
    """
    Tenant-domain service for WorkforceOS organization data.

    Important:

    This service must receive an AsyncSession that has already
    passed through the authorized tenant routing layer.

    It never resolves:

        workspace membership
        tenant database name
        tenant database URL

    Those security boundaries are handled before this service.
    """

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

        self.repository = EmployeeRepository(
            session
        )

    # =====================================================
    # DEPARTMENTS
    # =====================================================

    async def create_department(
        self,
        request: DepartmentCreateRequest,
    ) -> DepartmentResponse:
        await self._validate_department_uniqueness(
            name=request.name,
            code=request.code,
        )

        try:
            department = (
                await self.repository.create_department(
                    name=request.name,
                    code=request.code,
                    description=request.description,
                    is_active=True,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return DepartmentResponse(
            message="Department created.",
            department=self._department_public(
                department
            ),
        )

    async def list_departments(
        self,
        *,
        include_inactive: bool = False,
    ) -> DepartmentListResponse:
        departments = (
            await self.repository.list_departments(
                include_inactive=include_inactive,
            )
        )

        items = [
            self._department_public(
                department
            )
            for department in departments
        ]

        return DepartmentListResponse(
            departments=items,
            total=len(items),
        )

    async def get_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        department = (
            await self._require_department(
                department_id
            )
        )

        return DepartmentResponse(
            message="Department retrieved.",
            department=self._department_public(
                department
            ),
        )

    async def update_department(
        self,
        request: DepartmentUpdateRequest,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentResponse:
        department = (
            await self._require_department(
                department_id
            )
        )

        fields = request.model_fields_set

        if not fields:
            return DepartmentResponse(
                message="Department unchanged.",
                department=self._department_public(
                    department
                ),
            )

        values: dict[str, object] = {}

        if "name" in fields:
            if request.name is None:
                raise ValidationError(
                    "Department name cannot be cleared."
                )

            if (
                request.name.lower()
                != department.name.lower()
            ):
                if (
                    await self.repository.department_name_exists(
                        request.name,
                        exclude_id=department.id,
                    )
                ):
                    raise ConflictError(
                        "Department name is already in use."
                    )

            values["name"] = request.name

        if "code" in fields:
            if request.code is not None:
                if (
                    await self.repository.department_code_exists(
                        request.code,
                        exclude_id=department.id,
                    )
                ):
                    raise ConflictError(
                        "Department code is already in use."
                    )

            values["code"] = request.code

        if "description" in fields:
            values["description"] = (
                request.description
            )

        if "is_active" in fields:
            if request.is_active is None:
                raise ValidationError(
                    "Department active state cannot be null."
                )

            values["is_active"] = (
                request.is_active
            )

        try:
            department = (
                await self.repository.update_department(
                    department,
                    values=values,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return DepartmentResponse(
            message="Department updated.",
            department=self._department_public(
                department
            ),
        )

    async def delete_department(
        self,
        *,
        department_id: uuid.UUID,
    ) -> DepartmentDeleteResponse:
        department = (
            await self._require_department(
                department_id
            )
        )

        if not department.is_active:
            return DepartmentDeleteResponse(
                message="Department already inactive.",
                success=True,
            )

        try:
            await self.repository.deactivate_department(
                department
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return DepartmentDeleteResponse(
            message="Department deactivated.",
            success=True,
        )

    # =====================================================
    # TEAMS
    # =====================================================

    async def create_team(
        self,
        request: TeamCreateRequest,
    ) -> TeamResponse:
        if request.department_id is not None:
            await self._require_active_department(
                request.department_id
            )

        await self._validate_team_uniqueness(
            name=request.name,
            code=request.code,
            department_id=request.department_id,
        )

        try:
            team = await self.repository.create_team(
                name=request.name,
                code=request.code,
                description=request.description,
                department_id=request.department_id,
                is_active=True,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return TeamResponse(
            message="Team created.",
            team=self._team_public(
                team
            ),
        )

    async def list_teams(
        self,
        *,
        department_id: uuid.UUID | None = None,
        include_inactive: bool = False,
    ) -> TeamListResponse:
        if department_id is not None:
            await self._require_department(
                department_id
            )

        teams = await self.repository.list_teams(
            department_id=department_id,
            include_inactive=include_inactive,
        )

        items = [
            self._team_public(
                team
            )
            for team in teams
        ]

        return TeamListResponse(
            teams=items,
            total=len(items),
        )

    async def get_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        team = await self._require_team(
            team_id
        )

        return TeamResponse(
            message="Team retrieved.",
            team=self._team_public(
                team
            ),
        )

    async def update_team(
        self,
        request: TeamUpdateRequest,
        *,
        team_id: uuid.UUID,
    ) -> TeamResponse:
        team = await self._require_team(
            team_id
        )

        fields = request.model_fields_set

        if not fields:
            return TeamResponse(
                message="Team unchanged.",
                team=self._team_public(
                    team
                ),
            )

        target_department_id = (
            request.department_id
            if "department_id" in fields
            else team.department_id
        )

        if (
            target_department_id
            is not None
        ):
            await self._require_active_department(
                target_department_id
            )

        target_name = (
            request.name
            if "name" in fields
            else team.name
        )

        if target_name is None:
            raise ValidationError(
                "Team name cannot be cleared."
            )

        if (
            "name" in fields
            or "department_id" in fields
        ):
            if (
                await self.repository.team_name_exists(
                    name=target_name,
                    department_id=(
                        target_department_id
                    ),
                    exclude_id=team.id,
                )
            ):
                raise ConflictError(
                    "Team name is already in use "
                    "for this department."
                )

        values: dict[str, object] = {}

        if "name" in fields:
            values["name"] = target_name

        if "code" in fields:
            if request.code is not None:
                if (
                    await self.repository.team_code_exists(
                        request.code,
                        exclude_id=team.id,
                    )
                ):
                    raise ConflictError(
                        "Team code is already in use."
                    )

            values["code"] = request.code

        if "description" in fields:
            values["description"] = (
                request.description
            )

        if "department_id" in fields:
            values["department_id"] = (
                request.department_id
            )

        if "is_active" in fields:
            if request.is_active is None:
                raise ValidationError(
                    "Team active state cannot be null."
                )

            values["is_active"] = (
                request.is_active
            )

        try:
            team = await self.repository.update_team(
                team,
                values=values,
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return TeamResponse(
            message="Team updated.",
            team=self._team_public(
                team
            ),
        )

    async def delete_team(
        self,
        *,
        team_id: uuid.UUID,
    ) -> TeamDeleteResponse:
        team = await self._require_team(
            team_id
        )

        if not team.is_active:
            return TeamDeleteResponse(
                message="Team already inactive.",
                success=True,
            )

        try:
            await self.repository.deactivate_team(
                team
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return TeamDeleteResponse(
            message="Team deactivated.",
            success=True,
        )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    async def create_employee(
        self,
        request: EmployeeCreateRequest,
    ) -> EmployeeResponse:
        await self._validate_employee_uniqueness(
            employee_code=(
                request.employee_code
            ),
            work_email=(
                str(request.work_email)
                if request.work_email
                is not None
                else None
            ),
            user_id=request.user_id,
        )

        await self._validate_employee_organization(
            department_id=request.department_id,
            team_id=request.team_id,
        )

        if request.manager_id is not None:
            await self._require_active_employee(
                request.manager_id
            )

        self._validate_employee_lifecycle(
            employment_status=(
                request.employment_status
            ),
            hire_date=request.hire_date,
            termination_date=(
                request.termination_date
            ),
        )

        is_active = (
            request.employment_status
            != EMPLOYMENT_STATUS_TERMINATED
        )

        try:
            employee = (
                await self.repository.create_employee(
                    user_id=request.user_id,
                    employee_code=(
                        request.employee_code
                    ),
                    first_name=request.first_name,
                    last_name=request.last_name,
                    work_email=(
                        str(request.work_email)
                        if request.work_email
                        is not None
                        else None
                    ),
                    phone_number=(
                        request.phone_number
                    ),
                    avatar_url=request.avatar_url,
                    job_title=request.job_title,
                    employment_status=(
                        request.employment_status
                    ),
                    hire_date=request.hire_date,
                    termination_date=(
                        request.termination_date
                    ),
                    department_id=(
                        request.department_id
                    ),
                    team_id=request.team_id,
                    manager_id=request.manager_id,
                    is_active=is_active,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        employee = (
            await self._require_employee(
                employee.id
            )
        )

        return EmployeeResponse(
            message="Employee created.",
            employee=self._employee_public(
                employee
            ),
        )

    async def list_employees(
        self,
        *,
        department_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
        employment_status: str | None = None,
        include_inactive: bool = False,
        search: str | None = None,
    ) -> EmployeeListResponse:
        employees = (
            await self.repository.list_employees(
                department_id=department_id,
                team_id=team_id,
                manager_id=manager_id,
                employment_status=(
                    employment_status
                ),
                include_inactive=(
                    include_inactive
                ),
                search=search,
            )
        )

        items = [
            self._employee_public(
                employee
            )
            for employee in employees
        ]

        return EmployeeListResponse(
            employees=items,
            total=len(items),
        )

    async def get_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeDetailResponse:
        employee = await self._require_employee(
            employee_id
        )

        return EmployeeDetailResponse(
            employee=self._employee_public(
                employee
            ),
            department=(
                self._department_public(
                    employee.department
                )
                if employee.department
                is not None
                else None
            ),
            team=(
                self._team_public(
                    employee.team
                )
                if employee.team
                is not None
                else None
            ),
            manager=(
                self._employee_public(
                    employee.manager
                )
                if employee.manager
                is not None
                else None
            ),
        )

    async def update_employee(
        self,
        request: EmployeeUpdateRequest,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeResponse:
        employee = await self._require_employee(
            employee_id
        )

        fields = request.model_fields_set

        if not fields:
            return EmployeeResponse(
                message="Employee unchanged.",
                employee=self._employee_public(
                    employee
                ),
            )

        values: dict[str, object] = {}

        # -------------------------------------------------
        # GLOBAL USER LINK
        # -------------------------------------------------

        if "user_id" in fields:
            if (
                request.user_id is not None
                and (
                    await self.repository.employee_user_id_exists(
                        request.user_id,
                        exclude_id=employee.id,
                    )
                )
            ):
                raise ConflictError(
                    "This global user is already linked "
                    "to another employee."
                )

            values["user_id"] = (
                request.user_id
            )

        # -------------------------------------------------
        # EMPLOYEE CODE
        # -------------------------------------------------

        if "employee_code" in fields:
            if request.employee_code is None:
                raise ValidationError(
                    "Employee code cannot be cleared."
                )

            if (
                await self.repository.employee_code_exists(
                    request.employee_code,
                    exclude_id=employee.id,
                )
            ):
                raise ConflictError(
                    "Employee code is already in use."
                )

            values["employee_code"] = (
                request.employee_code
            )

        # -------------------------------------------------
        # NAME
        # -------------------------------------------------

        if "first_name" in fields:
            if request.first_name is None:
                raise ValidationError(
                    "Employee first name cannot be cleared."
                )

            values["first_name"] = (
                request.first_name
            )

        if "last_name" in fields:
            if request.last_name is None:
                raise ValidationError(
                    "Employee last name cannot be cleared."
                )

            values["last_name"] = (
                request.last_name
            )

        # -------------------------------------------------
        # CONTACT
        # -------------------------------------------------

        if "work_email" in fields:
            email = (
                str(request.work_email)
                if request.work_email
                is not None
                else None
            )

            if (
                email is not None
                and (
                    await self.repository.employee_work_email_exists(
                        email,
                        exclude_id=employee.id,
                    )
                )
            ):
                raise ConflictError(
                    "Employee work email is already in use."
                )

            values["work_email"] = email

        if "phone_number" in fields:
            values["phone_number"] = (
                request.phone_number
            )

        if "avatar_url" in fields:
            values["avatar_url"] = (
                request.avatar_url
            )

        if "job_title" in fields:
            values["job_title"] = (
                request.job_title
            )

        # -------------------------------------------------
        # ORGANIZATION STRUCTURE
        # -------------------------------------------------

        target_department_id = (
            request.department_id
            if "department_id" in fields
            else employee.department_id
        )

        target_team_id = (
            request.team_id
            if "team_id" in fields
            else employee.team_id
        )

        if (
            "department_id" in fields
            or "team_id" in fields
        ):
            await self._validate_employee_organization(
                department_id=(
                    target_department_id
                ),
                team_id=target_team_id,
            )

        if "department_id" in fields:
            values["department_id"] = (
                request.department_id
            )

        if "team_id" in fields:
            values["team_id"] = (
                request.team_id
            )

        # -------------------------------------------------
        # MANAGER
        # -------------------------------------------------

        if "manager_id" in fields:
            if (
                request.manager_id
                == employee.id
            ):
                raise ValidationError(
                    "An employee cannot be their own manager."
                )

            if request.manager_id is not None:
                await self._require_active_employee(
                    request.manager_id
                )

                if await self._would_create_manager_cycle(
                    employee_id=employee.id,
                    manager_id=request.manager_id,
                ):
                    raise ValidationError(
                        "Manager relationship would create "
                        "an organizational cycle."
                    )

            values["manager_id"] = (
                request.manager_id
            )

        # -------------------------------------------------
        # EMPLOYMENT LIFECYCLE
        # -------------------------------------------------

        target_status = (
            request.employment_status
            if "employment_status" in fields
            else employee.employment_status
        )

        target_hire_date = (
            request.hire_date
            if "hire_date" in fields
            else employee.hire_date
        )

        target_termination_date = (
            request.termination_date
            if "termination_date" in fields
            else employee.termination_date
        )

        if (
            "employment_status" in fields
            or "hire_date" in fields
            or "termination_date" in fields
        ):
            self._validate_employee_lifecycle(
                employment_status=(
                    target_status
                ),
                hire_date=(
                    target_hire_date
                ),
                termination_date=(
                    target_termination_date
                ),
            )

        if "employment_status" in fields:
            if request.employment_status is None:
                raise ValidationError(
                    "Employment status cannot be cleared."
                )

            values["employment_status"] = (
                request.employment_status
            )

            if (
                request.employment_status
                == EMPLOYMENT_STATUS_TERMINATED
            ):
                values["is_active"] = False

            elif "is_active" not in fields:
                values["is_active"] = True

        if "hire_date" in fields:
            values["hire_date"] = (
                request.hire_date
            )

        if "termination_date" in fields:
            values["termination_date"] = (
                request.termination_date
            )

        if "is_active" in fields:
            if request.is_active is None:
                raise ValidationError(
                    "Employee active state cannot be null."
                )

            if (
                target_status
                == EMPLOYMENT_STATUS_TERMINATED
                and request.is_active
            ):
                raise ValidationError(
                    "A terminated employee cannot be active."
                )

            values["is_active"] = (
                request.is_active
            )

        try:
            employee = (
                await self.repository.update_employee(
                    employee,
                    values=values,
                )
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        employee = (
            await self._require_employee(
                employee.id
            )
        )

        return EmployeeResponse(
            message="Employee updated.",
            employee=self._employee_public(
                employee
            ),
        )

    async def delete_employee(
        self,
        *,
        employee_id: uuid.UUID,
    ) -> EmployeeDeleteResponse:
        employee = await self._require_employee(
            employee_id
        )

        if not employee.is_active:
            return EmployeeDeleteResponse(
                message="Employee already inactive.",
                success=True,
            )

        try:
            await self.repository.deactivate_employee(
                employee
            )

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise

        return EmployeeDeleteResponse(
            message="Employee deactivated.",
            success=True,
        )

    # =====================================================
    # DUPLICATE VALIDATION
    # =====================================================

    async def _validate_department_uniqueness(
        self,
        *,
        name: str,
        code: str | None,
    ) -> None:
        if (
            await self.repository.department_name_exists(
                name
            )
        ):
            raise ConflictError(
                "Department name is already in use."
            )

        if (
            code is not None
            and (
                await self.repository.department_code_exists(
                    code
                )
            )
        ):
            raise ConflictError(
                "Department code is already in use."
            )

    async def _validate_team_uniqueness(
        self,
        *,
        name: str,
        code: str | None,
        department_id: uuid.UUID | None,
    ) -> None:
        if (
            await self.repository.team_name_exists(
                name=name,
                department_id=department_id,
            )
        ):
            raise ConflictError(
                "Team name is already in use "
                "for this department."
            )

        if (
            code is not None
            and (
                await self.repository.team_code_exists(
                    code
                )
            )
        ):
            raise ConflictError(
                "Team code is already in use."
            )

    async def _validate_employee_uniqueness(
        self,
        *,
        employee_code: str,
        work_email: str | None,
        user_id: uuid.UUID | None,
    ) -> None:
        if (
            await self.repository.employee_code_exists(
                employee_code
            )
        ):
            raise ConflictError(
                "Employee code is already in use."
            )

        if (
            work_email is not None
            and (
                await self.repository.employee_work_email_exists(
                    work_email
                )
            )
        ):
            raise ConflictError(
                "Employee work email is already in use."
            )

        if (
            user_id is not None
            and (
                await self.repository.employee_user_id_exists(
                    user_id
                )
            )
        ):
            raise ConflictError(
                "This global user is already linked "
                "to another employee."
            )

    # =====================================================
    # ORGANIZATION VALIDATION
    # =====================================================

    async def _validate_employee_organization(
        self,
        *,
        department_id: uuid.UUID | None,
        team_id: uuid.UUID | None,
    ) -> None:
        if department_id is not None:
            await self._require_active_department(
                department_id
            )

        if team_id is not None:
            team = await self._require_active_team(
                team_id
            )

            if (
                department_id is not None
                and team.department_id
                != department_id
            ):
                raise ValidationError(
                    "Team does not belong to "
                    "the selected department."
                )

            if (
                department_id is None
                and team.department_id
                is not None
            ):
                raise ValidationError(
                    "Employee department must match "
                    "the selected team's department."
                )

    # =====================================================
    # EMPLOYMENT VALIDATION
    # =====================================================

    def _validate_employee_lifecycle(
        self,
        *,
        employment_status: str,
        hire_date: date | None,
        termination_date: date | None,
    ) -> None:
        if (
            hire_date is not None
            and termination_date is not None
            and termination_date
            < hire_date
        ):
            raise ValidationError(
                "Termination date cannot be "
                "before hire date."
            )

        if (
            employment_status
            == EMPLOYMENT_STATUS_TERMINATED
            and termination_date is None
        ):
            raise ValidationError(
                "Termination date is required "
                "for a terminated employee."
            )

        if (
            employment_status
            != EMPLOYMENT_STATUS_TERMINATED
            and termination_date is not None
        ):
            raise ValidationError(
                "Termination date requires "
                "terminated employment status."
            )

    # =====================================================
    # MANAGER CYCLE PROTECTION
    # =====================================================

    async def _would_create_manager_cycle(
        self,
        *,
        employee_id: uuid.UUID,
        manager_id: uuid.UUID,
    ) -> bool:
        """
        Follow the proposed manager chain upward.

        If employee_id appears anywhere in that chain, assigning the
        manager would create a cycle.

        Example rejected structure:

            Alice -> Bob
            Bob   -> Carol
            Carol -> Alice
        """

        visited: set[uuid.UUID] = set()

        current_id: uuid.UUID | None = (
            manager_id
        )

        while current_id is not None:
            if current_id == employee_id:
                return True

            if current_id in visited:
                # Existing corrupt cycle. Do not extend it.
                return True

            visited.add(
                current_id
            )

            manager = (
                await self.repository.get_employee_by_id(
                    current_id
                )
            )

            if manager is None:
                return False

            current_id = (
                manager.manager_id
            )

        return False

    # =====================================================
    # REQUIRED OBJECTS
    # =====================================================

    async def _require_department(
        self,
        department_id: uuid.UUID,
    ) -> Department:
        department = (
            await self.repository.get_department_by_id(
                department_id
            )
        )

        if department is None:
            raise ResourceNotFound(
                "Department was not found."
            )

        return department

    async def _require_active_department(
        self,
        department_id: uuid.UUID,
    ) -> Department:
        department = (
            await self._require_department(
                department_id
            )
        )

        if not department.is_active:
            raise ValidationError(
                "Department is inactive."
            )

        return department

    async def _require_team(
        self,
        team_id: uuid.UUID,
    ) -> Team:
        team = (
            await self.repository.get_team_by_id(
                team_id
            )
        )

        if team is None:
            raise ResourceNotFound(
                "Team was not found."
            )

        return team

    async def _require_active_team(
        self,
        team_id: uuid.UUID,
    ) -> Team:
        team = await self._require_team(
            team_id
        )

        if not team.is_active:
            raise ValidationError(
                "Team is inactive."
            )

        return team

    async def _require_employee(
        self,
        employee_id: uuid.UUID,
    ) -> Employee:
        employee = (
            await self.repository.get_employee_by_id(
                employee_id
            )
        )

        if employee is None:
            raise ResourceNotFound(
                "Employee was not found."
            )

        return employee

    async def _require_active_employee(
        self,
        employee_id: uuid.UUID,
    ) -> Employee:
        employee = (
            await self._require_employee(
                employee_id
            )
        )

        if not employee.is_active:
            raise ValidationError(
                "Employee is inactive."
            )

        if (
            employee.employment_status
            == EMPLOYMENT_STATUS_TERMINATED
        ):
            raise ValidationError(
                "Terminated employee cannot "
                "be assigned as manager."
            )

        return employee

    # =====================================================
    # PUBLIC MAPPERS
    # =====================================================

    def _department_public(
        self,
        department: Department,
    ) -> DepartmentPublic:
        return DepartmentPublic.model_validate(
            department
        )

    def _team_public(
        self,
        team: Team,
    ) -> TeamPublic:
        return TeamPublic.model_validate(
            team
        )

    def _employee_public(
        self,
        employee: Employee,
    ) -> EmployeePublic:
        return EmployeePublic.model_validate(
            employee
        )


# =========================================================
# FACTORY
# =========================================================


def get_employee_service(
    session: AsyncSession,
) -> EmployeeService:
    return EmployeeService(
        session
    )


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "EmployeeService",
    "get_employee_service",
]