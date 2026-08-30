"""Evidence that tests at the repo root reach packages through their interface.

This exercises the scaffolded `billing` example, which exists only to carry the
boundary proof until a real package lands. Delete this file with it.
"""

from brotato_coaching.billing import Invoice, LineItem, format_amount, total_due
from brotato_coaching.billing.quote import estimate


def test_the_interface_is_enumerable() -> None:
    import brotato_coaching.billing as billing

    assert set(billing.__all__) == {"Invoice", "LineItem", "format_amount", "total_due"}


def test_a_total_is_reachable_without_naming_an_internal() -> None:
    invoice = Invoice(
        jurisdiction="UK",
        items=(LineItem(description="Coaching", unit_price_cents=1000, quantity=2),),
    )
    assert total_due(invoice) == estimate("UK", unit_price_cents=1000, quantity=2)
    assert format_amount(total_due(invoice)).startswith("24")
