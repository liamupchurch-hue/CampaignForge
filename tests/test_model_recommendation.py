"""The model recommendation is visual only; exact IDs remain API-safe."""
import unittest

from oracle_providers import (LOCAL_MODELS, LOCAL_MODEL_LABELS, RECOMMENDED_LOCAL_MODEL,
                              model_display_label, model_id_from_label)


class ModelRecommendationTests(unittest.TestCase):
    def test_recommendation_is_single_and_supported(self):
        self.assertEqual(RECOMMENDED_LOCAL_MODEL, "gemma3:12b")
        self.assertEqual(sum("(Recommended)" in label for label in LOCAL_MODEL_LABELS.values()), 1)
        self.assertIn(RECOMMENDED_LOCAL_MODEL, LOCAL_MODELS)

    def test_labels_roundtrip_to_exact_api_model_id(self):
        for model in LOCAL_MODELS:
            self.assertEqual(model_id_from_label(model_display_label(model)), model)

    def test_invalid_labels_fail_closed(self):
        with self.assertRaises(ValueError):
            model_id_from_label("gemma3:12b (Recommended) && other commands")


if __name__ == "__main__":
    unittest.main()
