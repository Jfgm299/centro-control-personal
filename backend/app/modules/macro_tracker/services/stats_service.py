from datetime import date, timedelta
from collections import defaultdict, Counter
from ..diary_entry import DiaryEntry
from ..macro_schema import (
    StatsResponse,
    DailyAverage,
    ProductFrequency,
    ProductResponse,
)


class StatsService:

    def calculate_stats(
        self, entries: list[DiaryEntry], period_days: int
    ) -> StatsResponse:
        if not entries:
            return StatsResponse(
                period_days=period_days,
                days_logged=0,
                total_entries=0,
                consistency_pct=0.0,
                daily_average=DailyAverage(
                    period_days=period_days,
                    days_logged=0,
                ),
                top_products=[],
            )

        # Agrupar entradas por día
        by_day: dict[date, list[DiaryEntry]] = defaultdict(list)
        for e in entries:
            by_day[e.entry_date].append(e)

        days_logged = len(by_day)
        consistency_pct = round(days_logged / period_days * 100, 1) if period_days else 0.0

        daily_average = self._calculate_daily_averages(by_day, period_days, days_logged)
        top_products  = self._calculate_top_products(entries)

        return StatsResponse(
            period_days=period_days,
            days_logged=days_logged,
            total_entries=len(entries),
            consistency_pct=consistency_pct,
            daily_average=daily_average,
            top_products=top_products,
        )

    def _calculate_daily_averages(
        self,
        by_day: dict[date, list[DiaryEntry]],
        period_days: int,
        days_logged: int,
    ) -> DailyAverage:
        def day_total(attr: str) -> float:
            return sum(
                sum(getattr(e, attr) or 0.0 for e in day_entries)
                for day_entries in by_day.values()
            )

        d = days_logged  # dividimos por días CON datos, no por período total
        return DailyAverage(
            period_days=period_days,
            days_logged=days_logged,
            avg_energy_kcal=    round(day_total("energy_kcal")     / d, 1),
            avg_proteins_g=     round(day_total("proteins_g")      / d, 1),
            avg_carbohydrates_g=round(day_total("carbohydrates_g") / d, 1),
            avg_fat_g=          round(day_total("fat_g")           / d, 1),
            avg_fiber_g=        round(day_total("fiber_g")         / d, 1),
        )

    def _calculate_top_products(
        self, entries: list[DiaryEntry], top_n: int = 10
    ) -> list[ProductFrequency]:
        counter: Counter = Counter(e.product_id for e in entries)
        # Mapa product_id → Product object (ya cargado via joinedload)
        products_map = {e.product_id: e.product for e in entries}

        result = []
        for product_id, count in counter.most_common(top_n):
            product = products_map.get(product_id)
            if product:
                result.append(ProductFrequency(
                    product=ProductResponse.model_validate(product),
                    entry_count=count,
                ))
        return result