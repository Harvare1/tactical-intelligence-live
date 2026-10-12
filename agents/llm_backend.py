"""Pluggable text-generation backend for the agent pipeline.

The hackathon brief asks for Microsoft Foundry / Azure AI Services, but this
repo ships with no API keys, so it must still run and demo offline. Setting
AZURE_FOUNDRY_ENDPOINT + AZURE_FOUNDRY_KEY (and optionally
AZURE_FOUNDRY_DEPLOYMENT) switches the pipeline to real model calls through
the Azure AI Foundry chat-completions REST API; without them it falls back
to a deterministic template backend so detectors, grounding and the demo UI
all keep working with zero external dependencies.
"""
import json
import os
import urllib.request
from abc import ABC, abstractmethod


class LLMBackend(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...


class TemplateBackend(LLMBackend):
    """Deterministic, offline fallback. Used whenever no Foundry credentials
    are configured, and in tests, so behavior never depends on network
    access or secrets."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # The template narrative generator never actually calls this path —
        # it builds grounded text directly — but pipeline components that
        # *do* want free-text generation (e.g. a future summarizer agent)
        # get a safe, obviously-synthetic string instead of a crash.
        return f"[template-backend] {user_prompt.splitlines()[0]}"


class AzureFoundryBackend(LLMBackend):
    def __init__(self, endpoint: str, api_key: str, deployment: str):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.deployment = deployment

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version=2024-06-01"
        body = json.dumps({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 200,
        }).encode()
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json", "api-key": self.api_key},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read())
        return payload["choices"][0]["message"]["content"]


def get_backend() -> LLMBackend:
    endpoint = os.environ.get("AZURE_FOUNDRY_ENDPOINT")
    api_key = os.environ.get("AZURE_FOUNDRY_KEY")
    deployment = os.environ.get("AZURE_FOUNDRY_DEPLOYMENT", "gpt-4o-mini")
    if endpoint and api_key:
        return AzureFoundryBackend(endpoint, api_key, deployment)
    return TemplateBackend()
