"""Database & Market Analytics Service for Comparable Properties & Area Market Statistics.
Powers LangGraph tools and Dashboard visual analytics from the 5,700+ verified listings repository.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from src.config import (
    PROPERTIES_DATASET_PATH,
    SOCIETY_BENCHMARK_PRICE,
    SOCIETY_TIERS,
    DEFAULT_SOCIETY_TIER,
    format_price_pkr,
)


class RealEstateDatabaseService:
    """In-memory spatial & transactional catalog query engine for listings and market trends."""

    def __init__(self, dataset_path: Path = PROPERTIES_DATASET_PATH):
        self.dataset_path = dataset_path
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Properties database not found at {dataset_path}")
        self.df = pd.read_csv(self.dataset_path)

        # Standardize strings
        self.df["city"] = self.df["city"].astype(str).str.strip().str.title()
        self.df["area_society"] = self.df["area_society"].astype(str).str.strip()
        self.df["property_type"] = self.df["property_type"].astype(str).str.strip().str.title()

        # Compute price_per_marla if missing
        if "price_per_marla" not in self.df.columns and "price_pkr" in self.df.columns:
            self.df["price_per_marla"] = self.df["price_pkr"] / self.df["area_marla"]

    def find_comparable_properties(
        self,
        city: str,
        area_society: str,
        area_marla: float,
        property_type: str = "House",
        bedrooms: Optional[int] = None,
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """Retrieve closest actual market listings from database matching physical specs."""
        city_clean = city.strip().title()
        soc_clean = area_society.strip()
        p_type_clean = property_type.strip().title()

        # 1. Exact match filter (City + Society + Type)
        subset = self.df[
            (self.df["city"] == city_clean)
            & (self.df["area_society"].str.lower() == soc_clean.lower())
            & (self.df["property_type"].str.lower() == p_type_clean.lower())
        ].copy()

        # 2. Relaxed fallback if sparse
        if len(subset) < max_results:
            subset = self.df[
                (self.df["city"] == city_clean)
                & (self.df["area_society"].str.lower() == soc_clean.lower())
            ].copy()

        if len(subset) < max_results:
            subset = self.df[self.df["city"] == city_clean].copy()

        if subset.empty:
            return []

        # Calculate distance / similarity metric
        area_diff = np.abs(subset["area_marla"] - float(area_marla)) / (float(area_marla) + 1e-5)
        bed_diff = (
            np.abs(subset["bedrooms"] - float(bedrooms)) / (float(bedrooms) + 1e-5)
            if bedrooms is not None
            else np.zeros(len(subset))
        )

        subset["match_distance"] = (0.70 * area_diff) + (0.30 * bed_diff)
        sorted_comps = subset.sort_values(by="match_distance").head(max_results)

        results = []
        for _, row in sorted_comps.iterrows():
            sim_score = max(50.0, round((1.0 - min(row["match_distance"], 0.8)) * 100.0, 1))
            price_val = float(row.get("price_pkr", row.get("price", 0)))
            results.append(
                {
                    "property_id": str(row.get("property_id", "PROP-COMP")),
                    "city": row["city"],
                    "area_society": row["area_society"],
                    "property_type": row["property_type"],
                    "area_marla": float(row["area_marla"]),
                    "bedrooms": int(row.get("bedrooms", 3)),
                    "bathrooms": int(row.get("bathrooms", 3)),
                    "age_years": int(row.get("age_years", 2)),
                    "is_corner": str(row.get("is_corner", "no")),
                    "price_pkr": price_val,
                    "price_formatted": format_price_pkr(price_val),
                    "price_per_marla_formatted": format_price_pkr(price_val / max(row["area_marla"], 1.0)) + " / marla",
                    "similarity_match_pct": f"{sim_score}%",
                    "summary": f"{row['area_marla']} Marla {row['property_type']} in {row['area_society']} ({row.get('bedrooms', 3)} Bed) -> {format_price_pkr(price_val)}",
                }
            )

        return results

    def get_market_statistics(
        self,
        city: str,
        area_society: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compute aggregated average price per marla, medians, and active inventory metrics."""
        city_clean = city.strip().title()

        if area_society:
            soc_clean = area_society.strip()
            subset = self.df[
                (self.df["city"] == city_clean)
                & (self.df["area_society"].str.lower() == soc_clean.lower())
            ]
            locality_label = f"{soc_clean}, {city_clean}"
        else:
            subset = self.df[self.df["city"] == city_clean]
            locality_label = city_clean

        if subset.empty:
            # Fallback to predefined benchmarks
            bench_ppm = SOCIETY_BENCHMARK_PRICE.get(area_society or "", 25_000_000) / 10.0
            return {
                "locality": locality_label,
                "city": city_clean,
                "area_society": area_society or "All Sectors",
                "total_listings_count": 0,
                "avg_price_per_marla_pkr": bench_ppm,
                "avg_price_per_marla_formatted": format_price_pkr(bench_ppm) + " / marla",
                "median_price_pkr": bench_ppm * 10,
                "median_price_formatted": format_price_pkr(bench_ppm * 10),
                "min_price_formatted": format_price_pkr(bench_ppm * 3),
                "max_price_formatted": format_price_pkr(bench_ppm * 30),
                "dominant_property_type": "House",
                "society_tier": SOCIETY_TIERS.get(area_society or "", DEFAULT_SOCIETY_TIER),
                "market_sentiment": "Stable Secondary Market (Benchmark rate applied)",
            }

        avg_ppm = float(subset["price_per_marla"].mean())
        median_price = float(subset["price_pkr"].median())
        min_price = float(subset["price_pkr"].min())
        max_price = float(subset["price_pkr"].max())
        dom_type = subset["property_type"].mode().iloc[0] if not subset["property_type"].empty else "House"
        tier = SOCIETY_TIERS.get(area_society or "", DEFAULT_SOCIETY_TIER)

        sentiment = "High Liquidity & Premium Demand" if "Tier 1" in tier else "Active Growth Corridor"

        return {
            "locality": locality_label,
            "city": city_clean,
            "area_society": area_society or "Metropolitan Overview",
            "total_listings_count": int(len(subset)),
            "avg_price_per_marla_pkr": avg_ppm,
            "avg_price_per_marla_formatted": format_price_pkr(avg_ppm) + " / marla",
            "median_price_pkr": median_price,
            "median_price_formatted": format_price_pkr(median_price),
            "min_price_formatted": format_price_pkr(min_price),
            "max_price_formatted": format_price_pkr(max_price),
            "dominant_property_type": dom_type,
            "society_tier": tier,
            "market_sentiment": sentiment,
        }

    def get_top_societies_by_city(self, city: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """Return ranking of societies by transaction volume and average price per marla."""
        city_clean = city.strip().title()
        subset = self.df[self.df["city"] == city_clean]
        if subset.empty:
            return []

        grouped = (
            subset.groupby("area_society")
            .agg(
                listing_count=("property_id", "count"),
                avg_price_per_marla=("price_per_marla", "mean"),
                median_price=("price_pkr", "median"),
            )
            .reset_index()
            .sort_values(by="listing_count", ascending=False)
            .head(top_n)
        )

        res = []
        for _, r in grouped.iterrows():
            res.append(
                {
                    "area_society": r["area_society"],
                    "listing_count": int(r["listing_count"]),
                    "avg_price_per_marla_formatted": format_price_pkr(r["avg_price_per_marla"]),
                    "median_price_formatted": format_price_pkr(r["median_price"]),
                }
            )
        return res


# Singleton instance
db_service = RealEstateDatabaseService()
