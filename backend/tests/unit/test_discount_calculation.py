"""
T027 — Testy jednostkowe: obliczanie rabatu.

Wzór: min(saldo, floor(kwota × pct / 100))
Opcjonalnie: min z limitem miesięcznym
"""
import pytest

from src.domain.codes import _calculate_discount


class TestCalculateDiscount:
    def test_basic_calculation(self):
        # 100 PLN * 20% = 20 PLN, saldo 150 → rabat 20
        result = _calculate_discount(100.0, 20.0, 150.0)
        assert result == 20.0

    def test_floor_rounding(self):
        # 100 PLN * 15% = 15.0 PLN — dokładne
        result = _calculate_discount(100.0, 15.0, 200.0)
        assert result == 15.0

    def test_floor_rounds_down(self):
        # 99 PLN * 10% = 9.9 → floor = 9
        result = _calculate_discount(99.0, 10.0, 200.0)
        assert result == 9.0

    def test_capped_by_balance(self):
        # 1000 PLN * 20% = 200, ale saldo = 50 → rabat = 50
        result = _calculate_discount(1000.0, 20.0, 50.0)
        assert result == 50.0

    def test_zero_balance_gives_zero(self):
        result = _calculate_discount(100.0, 20.0, 0.0)
        assert result == 0.0

    def test_zero_gross_gives_zero(self):
        result = _calculate_discount(0.0, 20.0, 100.0)
        assert result == 0.0

    def test_zero_discount_pct_gives_zero(self):
        result = _calculate_discount(100.0, 0.0, 100.0)
        assert result == 0.0

    def test_monthly_limit_caps_discount(self):
        # 1000 PLN * 20% = 200, saldo = 500, limit = 100 → rabat = 100
        result = _calculate_discount(1000.0, 20.0, 500.0, monthly_limit=100.0)
        assert result == 100.0

    def test_monthly_limit_none_ignored(self):
        # Brak limitu — nie wpływa na wynik
        result = _calculate_discount(100.0, 20.0, 150.0, monthly_limit=None)
        assert result == 20.0

    def test_full_balance_used_when_sufficient(self):
        # Saldo dokładnie równe obliczonemu rabatowi
        result = _calculate_discount(100.0, 20.0, 20.0)
        assert result == 20.0

    def test_high_discount_pct(self):
        # 100% rabatu — ograniczone saldem
        result = _calculate_discount(500.0, 100.0, 300.0)
        assert result == 300.0

    def test_precise_floor_behavior(self):
        # 333 PLN * 10% = 33.3 → floor = 33
        result = _calculate_discount(333.0, 10.0, 1000.0)
        assert result == 33.0
