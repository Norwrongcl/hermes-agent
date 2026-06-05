"""Azure AI Foundry image generation backend.

Routes Hermes ``image_generate`` calls through an Azure AI Foundry provider
endpoint such as Black Forest Labs FLUX.2 Pro. The active endpoint can be
configured either as a full URL:

    AZURE_IMAGE_ENDPOINT=https://<resource>.services.ai.azure.com/providers/blackforestlabs/v1/flux-2-pro

or as parts:

    AZURE_FOUNDRY_BASE_URL=https://<resource>.services.ai.azure.com
    AZURE_IMAGE_PROVIDER=blackforestlabs
    AZURE_IMAGE_DEPLOYMENT=flux-2-pro

Authentication uses a bearer token from ``AZURE_API_KEY`` or
``AZURE_FOUNDRY_API_KEY``.

Optional:

    AZURE_IMAGE_API_VERSION=preview
    AZURE_IMAGE_MODEL=FLUX.2-pro

The provider returns a local cached image path under
``$HERMES_HOME/cache/images/``.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

DEFAULT_API_VERSION = "preview"
DEFAULT_PROVIDER = "blackforestlabs"
DEFAULT_DEPLOYMENT = "flux-2-pro"
DEFAULT_MODEL = "FLUX.2-pro"

_MODELS: Dict[str, Dict[str, Any]] = {
    "FLUX.2-pro": {
        "display": "Azure FLUX.2 Pro",
        "speed": "provider dependent",
        "strengths": "Black Forest Labs photorealistic image generation",
    },
}

_SIZES = {
    "landscape": (1536, 864),
    "square": (1024, 1024),
    "portrait": (864, 1536),
}


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def _load_image_gen_config() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _resolve_model() -> Tuple[str, Dict[str, Any]]:
    env_override = _env("AZURE_IMAGE_MODEL")
    if env_override in _MODELS:
        return env_override, _MODELS[env_override]

    cfg = _load_image_gen_config()
    azure_cfg = cfg.get("azure-openai") if isinstance(cfg.get("azure-openai"), dict) else {}
    if isinstance(azure_cfg, dict):
        value = azure_cfg.get("model")
        if isinstance(value, str) and value in _MODELS:
            return value, _MODELS[value]

    top = cfg.get("model")
    if isinstance(top, str) and top in _MODELS:
        return top, _MODELS[top]

    return DEFAULT_MODEL, _MODELS[DEFAULT_MODEL]


class AzureOpenAIImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "azure-openai"

    @property
    def display_name(self) -> str:
        return "Azure AI Foundry"

    def is_available(self) -> bool:
        api_key = _env("AZURE_API_KEY") or _env("AZURE_FOUNDRY_API_KEY")
        endpoint = _env("AZURE_IMAGE_ENDPOINT")
        base_url = _env("AZURE_FOUNDRY_BASE_URL")
        return bool(api_key and (endpoint or base_url))

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": "Azure billing",
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Azure AI Foundry",
            "badge": "paid",
            "tag": "Black Forest Labs FLUX.2 Pro through Azure AI Foundry",
            "env_vars": [
                {
                    "key": "AZURE_FOUNDRY_BASE_URL",
                    "prompt": "Azure AI Foundry endpoint, e.g. https://<resource>.services.ai.azure.com",
                    "url": "https://ai.azure.com/",
                },
                {
                    "key": "AZURE_API_KEY",
                    "prompt": "Azure AI Foundry API key",
                    "url": "https://ai.azure.com/",
                },
                {
                    "key": "AZURE_IMAGE_DEPLOYMENT",
                    "prompt": "Azure image deployment slug, e.g. flux-2-pro",
                    "url": "https://ai.azure.com/",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider=self.name,
                aspect_ratio=aspect,
            )

        full_endpoint = _env("AZURE_IMAGE_ENDPOINT").rstrip("/")
        base_url = _env("AZURE_FOUNDRY_BASE_URL").rstrip("/")
        api_key = _env("AZURE_API_KEY") or _env("AZURE_FOUNDRY_API_KEY")
        provider = _env("AZURE_IMAGE_PROVIDER") or DEFAULT_PROVIDER
        deployment = _env("AZURE_IMAGE_DEPLOYMENT") or DEFAULT_DEPLOYMENT
        api_version = _env("AZURE_IMAGE_API_VERSION") or DEFAULT_API_VERSION

        if not api_key or not (full_endpoint or base_url):
            return error_response(
                error=(
                    "Azure image generation is not configured. Set AZURE_API_KEY "
                    "or AZURE_FOUNDRY_API_KEY, plus AZURE_IMAGE_ENDPOINT or "
                    "AZURE_FOUNDRY_BASE_URL in Coolify."
                ),
                error_type="auth_required",
                provider=self.name,
                aspect_ratio=aspect,
            )

        model_id, meta = _resolve_model()
        width, height = _SIZES.get(aspect, _SIZES["square"])

        if full_endpoint:
            url = f"{full_endpoint}?api-version={api_version}"
        else:
            url = f"{base_url}/providers/{provider}/v1/{deployment}?api-version={api_version}"
        payload: Dict[str, Any] = {
            "prompt": prompt,
            "model": model_id,
            "width": width,
            "height": height,
            "n": 1,
        }

        try:
            response = httpx.post(
                url,
                headers={
                    "authorization": f"Bearer {api_key}",
                    "content-type": "application/json",
                    "accept": "application/json",
                },
                json=payload,
                timeout=180.0,
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:1000] if exc.response is not None else ""
            return error_response(
                error=f"Azure image generation failed with HTTP {exc.response.status_code}: {detail}",
                error_type="http_status_error",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except Exception as exc:
            logger.debug("Azure image generation failed", exc_info=True)
            return error_response(
                error=f"Azure image generation failed: {exc}",
                error_type=type(exc).__name__,
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(data, list) or not data:
            return error_response(
                error="Azure returned no image data",
                error_type="empty_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        first = data[0] if isinstance(data[0], dict) else {}
        b64 = first.get("b64_json")
        image_url = first.get("url")
        revised_prompt = first.get("revised_prompt")

        if b64:
            try:
                image_ref = str(save_b64_image(b64, prefix=f"azure_{model_id}"))
            except Exception as exc:
                return error_response(
                    error=f"Could not save Azure image to cache: {exc}",
                    error_type="io_error",
                    provider=self.name,
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        elif image_url:
            try:
                image_ref = str(save_url_image(image_url, prefix=f"azure_{model_id}"))
            except Exception:
                image_ref = image_url
        else:
            return error_response(
                error="Azure response contained neither b64_json nor URL",
                error_type="empty_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {
            "provider_endpoint": provider,
            "deployment": deployment,
            "width": width,
            "height": height,
            "api_version": api_version,
        }
        if revised_prompt:
            extra["revised_prompt"] = revised_prompt

        return success_response(
            image=image_ref,
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider=self.name,
            extra=extra,
        )


def register(ctx) -> None:
    ctx.register_image_gen_provider(AzureOpenAIImageGenProvider())
