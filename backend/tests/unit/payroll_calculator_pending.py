from decimal import Decimal
from app.modules.payroll.schemas import PayrollInput,SalaryType,GraceMode
from app.modules.payroll.calculator import calculate_payroll
def test_salary():
    r=calculate_payroll(PayrollInput(salary_type=SalaryType.MONTHLY,base_salary=Decimal("50000"),working_days_in_period=22,shift_hours_per_day=Decimal("8"),late_minutes=13,grace_minutes=10,grace_mode=GraceMode.DEDUCT_EXCESS))
    assert r.chargeable_late_minutes==3
    assert r.late_deduction==Decimal("14.20")
