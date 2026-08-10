from __future__ import annotations

import unittest

from fragrance_intelligence.inventory import CollectionItem
from fragrance_intelligence.recommender import similar_fragrances


def fragrance(
    fragrance_id: str,
    *,
    family: str,
    notes: frozenset[str],
    seasons: frozenset[str],
    occasions: frozenset[str],
    longevity: float,
    projection: int,
) -> CollectionItem:
    return CollectionItem(
        fragrance_id=fragrance_id,
        house="Demo House",
        name=fragrance_id.title(),
        family=family,
        notes=notes,
        seasons=seasons,
        occasions=occasions,
        price_usd=100.0,
        bottle_ml=100.0,
        personal_rating=8.0,
        longevity_hours=longevity,
        projection=projection,
    )


class ExplainableRecommenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.collection = [
            fragrance(
                "target-01",
                family="fresh aromatic",
                notes=frozenset({"bergamot", "cedar", "juniper"}),
                seasons=frozenset({"spring", "summer"}),
                occasions=frozenset({"daily", "office"}),
                longevity=7.0,
                projection=3,
            ),
            fragrance(
                "close-02",
                family="fresh aromatic",
                notes=frozenset({"bergamot", "cedar", "musk"}),
                seasons=frozenset({"spring", "summer"}),
                occasions=frozenset({"daily", "office"}),
                longevity=7.5,
                projection=3,
            ),
            fragrance(
                "different-03",
                family="amber",
                notes=frozenset({"amber", "vanilla", "resin"}),
                seasons=frozenset({"fall", "winter"}),
                occasions=frozenset({"evening"}),
                longevity=10.0,
                projection=5,
            ),
        ]

    def test_excludes_target_and_ranks_closest_profile_first(self) -> None:
        recommendations = similar_fragrances("target-01", self.collection)

        self.assertEqual(
            [recommendation.fragrance_id for recommendation in recommendations],
            ["close-02", "different-03"],
        )
        self.assertNotIn("target-01", [entry.fragrance_id for entry in recommendations])
        self.assertGreater(recommendations[0].score, recommendations[1].score)

    def test_returns_components_and_plain_language_reasons(self) -> None:
        recommendation = similar_fragrances("target-01", self.collection, limit=1)[0]

        self.assertEqual(
            set(recommendation.components),
            {"family", "longevity", "notes", "occasion", "projection", "season"},
        )
        self.assertTrue(any("bergamot" in reason for reason in recommendation.reasons))
        self.assertTrue(any("fresh aromatic" in reason for reason in recommendation.reasons))
        self.assertTrue(all(0.0 <= value <= 1.0 for value in recommendation.components.values()))

    def test_ties_are_stable_by_identifier(self) -> None:
        duplicate_a = fragrance(
            "alpha-04",
            family="fresh aromatic",
            notes=frozenset({"bergamot", "cedar", "musk"}),
            seasons=frozenset({"spring", "summer"}),
            occasions=frozenset({"daily", "office"}),
            longevity=7.5,
            projection=3,
        )
        duplicate_z = fragrance(
            "zulu-05",
            family="fresh aromatic",
            notes=frozenset({"bergamot", "cedar", "musk"}),
            seasons=frozenset({"spring", "summer"}),
            occasions=frozenset({"daily", "office"}),
            longevity=7.5,
            projection=3,
        )

        recommendations = similar_fragrances(
            "target-01", [self.collection[0], duplicate_z, duplicate_a]
        )

        self.assertEqual(
            [recommendation.fragrance_id for recommendation in recommendations],
            ["alpha-04", "zulu-05"],
        )

    def test_rejects_unknown_target_or_invalid_limit(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown target"):
            similar_fragrances("missing", self.collection)
        with self.assertRaisesRegex(ValueError, "limit must be greater than 0"):
            similar_fragrances("target-01", self.collection, limit=0)


if __name__ == "__main__":
    unittest.main()
