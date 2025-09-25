import logging

from django.conf import settings
from google import generativeai as genai
from google.generativeai.types import GenerateContentResponse


class GeminiClient:
    def __init__(
        self,
        model: str,
        prompt: str,
        temperature: float,
        max_tokens: int | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.genai = None
        self.genconfig = None

        self._logger = logger or logging.getLogger(__name__)

    def _set_genai(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.genai = genai.GenerativeModel(self.model)

    def _set_genconfig(self):
        self.genconfig = genai.GenerationConfig(temperature=self.temperature, max_output_tokens=self.max_tokens)

    def generate(self, context: dict[str, str] | None = None) -> GenerateContentResponse:
        self._set_genai()
        self._set_genconfig()
        self._logger.info("Making API request to LLM.")

        return self.genai.generate_content(self.prompt.format(**context), generation_config=self.genconfig)
