from django.test import SimpleTestCase

from ai.openai_models import (
    ALLOWED_OPENAI_MODEL_IDS,
    DEFAULT_OPENAI_MODEL,
    normalize_openai_model,
)


class OpenAIModelsCatalogTests(SimpleTestCase):
    def test_default_model_is_allowed(self):
        self.assertIn(DEFAULT_OPENAI_MODEL, ALLOWED_OPENAI_MODEL_IDS)

    def test_normalize_accepts_recommended_models(self):
        for model_id in ("gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-4.1-mini"):
            self.assertEqual(normalize_openai_model(model_id), model_id)

    def test_normalize_rejects_unknown_model(self):
        with self.assertRaises(ValueError):
            normalize_openai_model("gpt-unknown")
