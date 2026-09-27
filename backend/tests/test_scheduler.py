import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import Settings
from app.scheduler import build_scheduler, daily_report, remind_and_retry


class _RecordingNotifier:
    def __init__(self) -> None:
        self.order_created_calls: list = []
        self.reminder_calls: list = []
        self.daily_report_calls: list = []

    async def order_created(self, order):
        self.order_created_calls.append(order)

    async def status_changed(self, order):
        pass

    async def reminder(self, orders):
        self.reminder_calls.append(orders)

    async def daily_report(self, orders):
        self.daily_report_calls.append(orders)


def _settings(**overrides):
    fields = dict(reminder_first_hours=2, reminder_repeat_hours=4, reminder_check_minutes=5)
    fields.update(overrides)
    return Settings(**fields)


async def test_new_order_at_1h59_gets_no_reminder(session_factory, make_order):
    created_at = dt.datetime(2026, 1, 1, 10, 0, 0)
    await make_order(status="new", created_at=created_at)
    notifier = _RecordingNotifier()
    now = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=1, minutes=59)

    await remind_and_retry(session_factory, notifier, _settings(), now)

    assert notifier.reminder_calls == []


async def test_new_order_at_2h01_gets_reminder_and_persists_last_reminded_at(session_factory, make_order):
    created_at = dt.datetime(2026, 1, 1, 10, 0, 0)
    order = await make_order(status="new", created_at=created_at)
    notifier = _RecordingNotifier()
    now = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=2, minutes=1)

    await remind_and_retry(session_factory, notifier, _settings(), now)

    assert len(notifier.reminder_calls) == 1
    reminded_ids = {o.id for o in notifier.reminder_calls[0]}
    assert order.id in reminded_ids

    async with session_factory() as session:
        from app.models import Order

        refreshed = await session.get(Order, order.id)
    assert refreshed.last_reminded_at is not None


async def test_new_order_at_plus_3h_no_second_reminder(session_factory, make_order):
    created_at = dt.datetime(2026, 1, 1, 10, 0, 0)
    await make_order(status="new", created_at=created_at)
    notifier = _RecordingNotifier()
    settings = _settings()

    first_reminder_time = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=2, minutes=1)
    await remind_and_retry(session_factory, notifier, settings, first_reminder_time)
    assert len(notifier.reminder_calls) == 1

    plus_3h = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=3)
    await remind_and_retry(session_factory, notifier, settings, plus_3h)
    assert len(notifier.reminder_calls) == 1  # still just the one from before


async def test_new_order_at_plus_4h01_gets_repeat_reminder(session_factory, make_order):
    created_at = dt.datetime(2026, 1, 1, 10, 0, 0)
    await make_order(status="new", created_at=created_at)
    notifier = _RecordingNotifier()
    settings = _settings()

    first_reminder_time = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=2, minutes=1)
    await remind_and_retry(session_factory, notifier, settings, first_reminder_time)

    plus_4h01 = first_reminder_time + dt.timedelta(hours=4, minutes=1)
    await remind_and_retry(session_factory, notifier, settings, plus_4h01)
    assert len(notifier.reminder_calls) == 2


async def test_accepted_order_never_reminded(session_factory, make_order):
    created_at = dt.datetime(2026, 1, 1, 10, 0, 0)
    await make_order(status="accepted", created_at=created_at)
    notifier = _RecordingNotifier()
    now = created_at.replace(tzinfo=dt.timezone.utc) + dt.timedelta(hours=10)

    await remind_and_retry(session_factory, notifier, _settings(), now)

    assert notifier.reminder_calls == []


async def test_not_notified_order_is_resent(session_factory, make_order):
    order = await make_order(status="new", admin_notified=False)
    notifier = _RecordingNotifier()
    now = dt.datetime.now(dt.timezone.utc)

    await remind_and_retry(session_factory, notifier, _settings(), now)

    resent_ids = {o.id for o in notifier.order_created_calls}
    assert order.id in resent_ids


async def test_daily_report_forwards_open_orders_grouped_by_notifier(session_factory, make_order):
    await make_order(status="new")
    await make_order(status="delivered")  # final, not open
    notifier = _RecordingNotifier()

    await daily_report(session_factory, notifier, _settings(), dt.datetime.now(dt.timezone.utc))

    assert len(notifier.daily_report_calls) == 1
    statuses = {o.status for o in notifier.daily_report_calls[0]}
    assert statuses == {"new"}


async def test_daily_report_empty_still_calls_notifier_with_empty_list(session_factory):
    notifier = _RecordingNotifier()

    await daily_report(session_factory, notifier, _settings(), dt.datetime.now(dt.timezone.utc))

    assert notifier.daily_report_calls == [[]]


async def test_remind_and_retry_rejects_naive_now(session_factory):
    notifier = _RecordingNotifier()
    naive_now = dt.datetime(2026, 1, 1, 12, 0, 0)

    import pytest

    with pytest.raises(ValueError):
        await remind_and_retry(session_factory, notifier, _settings(), naive_now)


async def test_daily_report_rejects_naive_now(session_factory):
    notifier = _RecordingNotifier()
    naive_now = dt.datetime(2026, 1, 1, 12, 0, 0)

    import pytest

    with pytest.raises(ValueError):
        await daily_report(session_factory, notifier, _settings(), naive_now)


def test_build_scheduler_registers_interval_and_cron_jobs():
    settings = _settings(daily_report_time="09:00", timezone="Asia/Tashkent", reminder_check_minutes=5)
    scheduler = build_scheduler(lambda: None, _RecordingNotifier(), settings)
    assert isinstance(scheduler, AsyncIOScheduler)
    jobs = scheduler.get_jobs()
    assert len(jobs) == 2
    trigger_types = {type(job.trigger).__name__ for job in jobs}
    assert trigger_types == {"IntervalTrigger", "CronTrigger"}

    cron_job = next(j for j in jobs if type(j.trigger).__name__ == "CronTrigger")
    field_by_name = {f.name: f for f in cron_job.trigger.fields}
    assert str(field_by_name["hour"]) == "9"
    assert str(field_by_name["minute"]) == "0"
    assert str(cron_job.trigger.timezone) == "Asia/Tashkent"
