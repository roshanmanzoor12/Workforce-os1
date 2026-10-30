from datetime import time

from app.modules.shifts.service import (
    minutes_between,
)


def test_regular_shift_minutes():
    assert (
        minutes_between(
            time(9, 0),
            time(17, 0),
            overnight=False,
        )
        == 480
    )


def test_nine_to_six_shift_minutes():
    assert (
        minutes_between(
            time(9, 0),
            time(18, 0),
            overnight=False,
        )
        == 540
    )


def test_overnight_shift_minutes():
    assert (
        minutes_between(
            time(22, 0),
            time(6, 0),
            overnight=True,
        )
        == 480
    )


def test_overnight_is_detected_when_end_is_before_start():
    assert (
        minutes_between(
            time(23, 30),
            time(7, 30),
            overnight=True,
        )
        == 480
    )


def test_half_day_shift():
    assert (
        minutes_between(
            time(8, 0),
            time(12, 0),
            overnight=False,
        )
        == 240
    )