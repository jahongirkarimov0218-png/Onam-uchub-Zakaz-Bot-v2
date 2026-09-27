from app.notify import NullNotifier, Notifier


async def test_null_notifier_satisfies_protocol_and_is_a_noop(caplog):
    notifier: Notifier = NullNotifier()
    caplog.set_level("INFO")

    await notifier.order_created(object())
    await notifier.status_changed(object())
    await notifier.reminder([object(), object()])
    await notifier.daily_report([object()])

    # no-op: nothing raised, and it logged instead of doing anything else
    assert caplog.records
