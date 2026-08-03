"""Natural-language explanation generation. Two interchangeable strategies:

  GeminiExplanationService     - calls the Gemini API for fluent, contextual prose
  RuleBasedExplanationService  - deterministic template, used when no API key
                                   is configured so the app is fully usable offline

Both implement IExplanationService, so callers (the chat + report services)
never need to know or care which one is active. This is the Strategy pattern
satisfying the Liskov Substitution Principle.
"""
from __future__ import annotations

import logging

import httpx

from app.domain.entities import PredictionOutcome, SensorReading
from app.domain.enums import FailureType
from app.services.interfaces import IExplanationService

logger = logging.getLogger("factorypulse.explanation")

_GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


class GeminiExplanationService(IExplanationService):
    def __init__(self, api_key: str, model: str, fallback: IExplanationService):
        self._api_key = api_key
        self._model = model
        self._fallback = fallback

    def explain(self, machine_id: str, reading: SensorReading, outcome: PredictionOutcome) -> str:
        prompt = (
            "You are a plant maintenance copilot. In 2-3 sentences, explain to a "
            "plant manager why the following machine was flagged, in plain "
            "operational language, and end with one concrete next step.\n\n"
            f"Machine: {machine_id}\n"
            f"Predicted failure type: {outcome.predicted_failure_type.display_name}\n"
            f"Failure probability: {outcome.failure_probability * 100:.1f}%\n"
            f"Health score: {outcome.health_score:.0f}/100 ({outcome.health_status})\n"
            f"Air temperature: {reading.air_temperature_k:.1f} K\n"
            f"Process temperature: {reading.process_temperature_k:.1f} K\n"
            f"Rotational speed: {reading.rotational_speed_rpm:.0f} rpm\n"
            f"Torque: {reading.torque_nm:.1f} Nm\n"
            f"Tool wear: {reading.tool_wear_min:.0f} min\n"
        )
        return self._call_gemini(prompt) or self._fallback.explain(machine_id, reading, outcome)

    def answer_question(self, question: str, context: str) -> str:
        prompt = (
            "You are FactoryPulse AI, a manufacturing maintenance copilot. Answer "
            "the plant manager's question using only the machine data below. Be "
            "concise and specific to the machine IDs mentioned.\n\n"
            f"Machine data:\n{context}\n\nQuestion: {question}"
        )
        return self._call_gemini(prompt) or self._fallback.answer_question(question, context)

    def _call_gemini(self, prompt: str) -> str | None:
        url = _GEMINI_ENDPOINT.format(model=self._model)
        try:
            response = httpx.post(
                url,
                params={"key": self._api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (httpx.HTTPError, KeyError, IndexError) as exc:
            logger.warning("Gemini call failed, falling back to rule-based text: %s", exc)
            return None


class RuleBasedExplanationService(IExplanationService):
    """Deterministic explanations. No network call, no API key required —
    this is what keeps the whole platform runnable with zero external
    dependencies, and it's what Gemini falls back to on any API failure."""

    def explain(self, machine_id: str, reading: SensorReading, outcome: PredictionOutcome) -> str:
        if outcome.predicted_failure_type == FailureType.NONE:
            return (
                f"{machine_id} is operating normally with a health score of "
                f"{outcome.health_score:.0f}/100. No corrective action needed."
            )
        temp_delta = reading.process_temperature_k - reading.air_temperature_k
        urgency = "Schedule maintenance within the next shift." if outcome.health_score < 60 else (
            "Add to the upcoming maintenance window."
        )
        return (
            f"{machine_id} has a {outcome.failure_probability * 100:.0f}% probability of "
            f"{outcome.predicted_failure_type.display_name} due to a process/air temperature "
            f"differential of {temp_delta:.1f}K, {reading.tool_wear_min:.0f} min of tool wear, "
            f"and {reading.torque_nm:.1f} Nm of torque. {urgency}"
        )

    def answer_question(self, question: str, context: str) -> str:
        return (
            "Here is the relevant machine data I found for your question:\n\n"
            f"{context}\n\n"
            "(Connect a GEMINI_API_KEY to get a natural-language summary of this data.)"
        )
