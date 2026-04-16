"""
Multi-provider Logo generation layer.

Follows the same Provider Pattern + Fallback chain used in ppt_providers.py.

Providers (strategy pattern):
    - OpenAILogoProvider    -> OpenAI images.generate (DALL-E 3 / GPT Image)
    - IdeogramProvider      -> Ideogram V3 API (https://api.ideogram.ai)
    - RecraftProvider       -> Recraft V4 via fal.ai (vector SVG logos)

Primary provider is selected via the `logo_provider_config` system setting;
unknown / unconfigured providers automatically fall back so the platform
never fails to deliver a logo set.
"""
from __future__ import annotations

import asyncio
import base64
import os
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Result dataclass ─────────────────────────────────────────────────────────
@dataclass
class LogoResult:
    success: bool
    provider: str
    variants: List[Dict[str, Any]] = field(default_factory=list)
    # Each variant: {index: int, png_url: str, svg_url: str|None, prompt: str}
    error: str = ""


# ── Prompt builder ───────────────────────────────────────────────────────────
_STYLE_HINTS = {
    "modern":   "clean lines, geometric shapes, flat design, contemporary feel",
    "minimal":  "ultra-minimalist, single icon, maximum whitespace, simple geometry",
    "luxury":   "elegant serif typography, gold accents, refined, premium feel",
    "tech":     "futuristic, circuit-inspired, gradient blues/purples, sharp edges",
    "natural":  "organic shapes, leaf or nature motifs, earth tones, hand-drawn feel",
    "playful":  "rounded shapes, vibrant colors, friendly, cartoon-like elements",
}


def build_logo_prompt(
    brand_name: str,
    style: str = "modern",
    primary_color: str = "",
    include_text: bool = True,
    industry: str = "",
) -> str:
    """Build a professional logo generation prompt."""
    style_hint = _STYLE_HINTS.get(style, _STYLE_HINTS["modern"])

    parts = [
        f"Professional logo design for a brand called '{brand_name}'.",
        f"Style: {style} — {style_hint}.",
    ]
    if industry:
        parts.append(f"Industry: {industry}.")
    if primary_color:
        parts.append(f"Primary brand color: {primary_color}.")
    if include_text:
        parts.append(
            f"Include the brand name '{brand_name}' as part of the logo with clear, legible typography."
        )
    else:
        parts.append(
            "Icon-only mark, no text or lettering in the design."
        )
    parts.append(
        "Isolated on a pure white background, high resolution, vector-quality, "
        "suitable for print and digital use."
    )
    return " ".join(parts)


# ── Abstract base ────────────────────────────────────────────────────────────
class BaseLogoProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        *,
        prompt: str,
        brand_name: str,
        style: str,
        include_text: bool,
        variant_count: int,
        primary_color: str,
        api_key: str,
    ) -> LogoResult:
        """Generate logo variants. Returns LogoResult with list of image URLs."""

    def __repr__(self) -> str:
        return f"<LogoProvider {self.name}>"


# ── OpenAI (DALL-E 3 / GPT Image) ───────────────────────────────────────────
class OpenAILogoProvider(BaseLogoProvider):
    name = "openai"

    def __init__(self, model: str = "dall-e-3"):
        self.model = model

    async def generate(
        self,
        *,
        prompt: str,
        brand_name: str,
        style: str,
        include_text: bool,
        variant_count: int,
        primary_color: str,
        api_key: str,
    ) -> LogoResult:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        variants: List[Dict[str, Any]] = []
        last_err = ""

        # DALL-E 3 only supports n=1 per call, so loop for each variant.
        for idx in range(variant_count):
            body: Dict[str, Any] = {
                "model": self.model,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "quality": "hd",
                "response_format": "url",
            }
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(
                        "https://api.openai.com/v1/images/generations",
                        headers=headers,
                        json=body,
                    )
                    if r.status_code >= 400:
                        last_err = f"OpenAI [{r.status_code}]: {r.text[:300]}"
                        print(f"[OpenAILogo] variant {idx} failed: {last_err}")
                        continue
                    data = r.json()
                    img = data.get("data", [{}])[0]
                    url = img.get("url") or ""
                    # If response_format was b64_json, we'd get that instead
                    if not url and img.get("b64_json"):
                        url = f"data:image/png;base64,{img['b64_json']}"
                    variants.append({
                        "index": idx,
                        "png_url": url,
                        "svg_url": None,
                        "prompt": prompt,
                    })
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                print(f"[OpenAILogo] variant {idx} error: {exc}")

        if not variants:
            return LogoResult(success=False, provider=self.name, error=last_err)
        return LogoResult(success=True, provider=self.name, variants=variants)


# ── Ideogram V3 ─────────────────────────────────────────────────────────────
class IdeogramProvider(BaseLogoProvider):
    name = "ideogram"

    def __init__(self, model: str = "V_3"):
        self.model = model

    async def generate(
        self,
        *,
        prompt: str,
        brand_name: str,
        style: str,
        include_text: bool,
        variant_count: int,
        primary_color: str,
        api_key: str,
    ) -> LogoResult:
        import httpx

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        body: Dict[str, Any] = {
            "prompt": prompt,
            "model": self.model,
            "aspect_ratio": "1:1",
            "style": "design",
            "negative_prompt": "blurry, low quality, distorted text, watermark, photograph",
            "num_images": min(variant_count, 4),  # Ideogram max 4 per request
        }

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                r = await client.post(
                    "https://api.ideogram.ai/v1/ideogram-v3/generate",
                    headers=headers,
                    json=body,
                )
                if r.status_code >= 400:
                    err = f"Ideogram [{r.status_code}]: {r.text[:300]}"
                    return LogoResult(success=False, provider=self.name, error=err)

                data = r.json()
                images = data.get("data", [])
                variants = [
                    {
                        "index": idx,
                        "png_url": img.get("url", ""),
                        "svg_url": None,
                        "prompt": prompt,
                    }
                    for idx, img in enumerate(images)
                ]
                if not variants:
                    return LogoResult(
                        success=False, provider=self.name,
                        error="Ideogram returned no images",
                    )
                return LogoResult(success=True, provider=self.name, variants=variants)
        except Exception as exc:  # noqa: BLE001
            return LogoResult(success=False, provider=self.name, error=str(exc))


# ── Recraft V4 (fal.ai — vector SVG) ────────────────────────────────────────
class RecraftProvider(BaseLogoProvider):
    """
    Calls fal.ai's Recraft V4 text-to-vector endpoint for SVG logo output.
    """
    name = "recraft"

    def __init__(self, model: str = "fal-ai/recraft/v4/text-to-vector"):
        self.model = model

    async def generate(
        self,
        *,
        prompt: str,
        brand_name: str,
        style: str,
        include_text: bool,
        variant_count: int,
        primary_color: str,
        api_key: str,
    ) -> LogoResult:
        import httpx

        # fal.ai uses "Key" authorization scheme
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Key {api_key}",
        }
        endpoint = f"https://fal.run/{self.model}"

        variants: List[Dict[str, Any]] = []
        last_err = ""

        # fal.ai recraft typically returns one image per call
        for idx in range(variant_count):
            body: Dict[str, Any] = {
                "prompt": prompt,
            }
            if primary_color:
                body["colors"] = [primary_color]

            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(endpoint, headers=headers, json=body)
                    if r.status_code >= 400:
                        last_err = f"Recraft [{r.status_code}]: {r.text[:300]}"
                        print(f"[Recraft] variant {idx} failed: {last_err}")
                        continue
                    data = r.json()
                    # fal.ai returns images in data.images[] or data.image
                    images = data.get("images", [])
                    if not images and data.get("image"):
                        images = [data["image"]]
                    for img in images:
                        url = img.get("url", "") if isinstance(img, dict) else str(img)
                        variants.append({
                            "index": idx,
                            "png_url": url,
                            "svg_url": url if url.endswith(".svg") else None,
                            "prompt": prompt,
                        })
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                print(f"[Recraft] variant {idx} error: {exc}")

        if not variants:
            return LogoResult(success=False, provider=self.name, error=last_err)
        return LogoResult(success=True, provider=self.name, variants=variants)


# ── Factory + fallback chain ─────────────────────────────────────────────────
def _build(name: str, cfg: dict) -> Optional[BaseLogoProvider]:
    name = (name or "").strip().lower()
    if name == "openai":
        key = (cfg.get("openai_api_key") or "").strip()
        if not key:
            print("[LogoProvider] openai_api_key missing — cannot build openai")
            return None
        return OpenAILogoProvider(model=cfg.get("openai_model") or "dall-e-3")
    if name == "ideogram":
        key = (cfg.get("ideogram_api_key") or "").strip()
        if not key:
            print("[LogoProvider] ideogram_api_key missing — cannot build ideogram")
            return None
        return IdeogramProvider(model=cfg.get("ideogram_model") or "V_3")
    if name == "recraft":
        key = (cfg.get("recraft_api_key") or "").strip()
        if not key:
            print("[LogoProvider] recraft_api_key missing — cannot build recraft")
            return None
        return RecraftProvider(model=cfg.get("recraft_model") or "fal-ai/recraft/v4/text-to-vector")
    print(f"[LogoProvider] Unknown provider '{name}'")
    return None


def _api_key_for(name: str, cfg: dict) -> str:
    """Retrieve the correct API key for a given provider name."""
    name = (name or "").strip().lower()
    if name == "openai":
        return (cfg.get("openai_api_key") or "").strip()
    if name == "ideogram":
        return (cfg.get("ideogram_api_key") or "").strip()
    if name == "recraft":
        return (cfg.get("recraft_api_key") or "").strip()
    return ""


async def generate_via_providers(
    *,
    brand_name: str,
    prompt: str,
    style: str = "modern",
    include_text: bool = True,
    variant_count: int = 3,
    primary_color: str = "",
    db=None,
) -> tuple[LogoResult, str]:
    """
    Try primary provider, then fallback, then openai as last resort.
    Config is loaded from the DB (system_settings.logo_provider_config), with
    env vars as the deployment-time default. Returns (LogoResult, provider_name).
    """
    from services.logo_settings import load_config
    cfg = load_config(db)
    primary_name  = cfg.get("provider") or "openai"
    fallback_name = cfg.get("fallback") or "openai"

    chain: list[BaseLogoProvider] = []
    for nm in (primary_name, fallback_name, "openai"):
        p = _build(nm, cfg)
        if p and not any(existing.name == p.name for existing in chain):
            chain.append(p)

    last_err: Optional[str] = None
    for provider in chain:
        try:
            print(f"[LogoProvider] -> trying {provider.name}")
            result = await provider.generate(
                prompt=prompt,
                brand_name=brand_name,
                style=style,
                include_text=include_text,
                variant_count=variant_count,
                primary_color=primary_color,
                api_key=_api_key_for(provider.name, cfg),
            )
            if result.success:
                print(f"[LogoProvider] OK {provider.name} — {len(result.variants)} variants")
                return result, provider.name
            last_err = result.error
            print(f"[LogoProvider] X {provider.name} failed: {result.error}")
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
            print(f"[LogoProvider] X {provider.name} error: {exc}")

    return LogoResult(
        success=False, provider="none", error=f"All logo providers failed. Last: {last_err}"
    ), "none"


# ── Admin / debug: list + test ───────────────────────────────────────────────
def list_providers(db=None) -> list[dict]:
    """Return status of every provider (for an admin endpoint)."""
    from services.logo_settings import load_config
    cfg = load_config(db)
    primary  = cfg.get("provider") or "openai"
    fallback = cfg.get("fallback") or "openai"

    def _role(n: str) -> str:
        if n == primary:  return "primary"
        if n == fallback: return "fallback"
        return "inactive"

    return [
        {
            "name":      "openai",
            "label":     "OpenAI DALL-E / GPT Image",
            "available": bool((cfg.get("openai_api_key") or "").strip()),
            "role":      _role("openai"),
        },
        {
            "name":      "ideogram",
            "label":     "Ideogram V3 (Design-focused)",
            "available": bool((cfg.get("ideogram_api_key") or "").strip()),
            "role":      _role("ideogram"),
        },
        {
            "name":      "recraft",
            "label":     "Recraft V4 (Vector SVG via fal.ai)",
            "available": bool((cfg.get("recraft_api_key") or "").strip()),
            "role":      _role("recraft"),
        },
    ]


async def test_provider(name: str, db=None) -> dict:
    """Ping a provider with a minimal request to verify connectivity."""
    from services.logo_settings import load_config
    cfg = load_config(db)
    provider = _build(name, cfg)
    if not provider:
        return {"ok": False, "provider": name, "error": "provider not configured"}

    api_key = _api_key_for(name, cfg)
    try:
        result = await provider.generate(
            prompt="Simple geometric circle logo, minimal, white background",
            brand_name="Test",
            style="minimal",
            include_text=False,
            variant_count=1,
            primary_color="",
            api_key=api_key,
        )
        if result.success:
            return {"ok": True, "provider": provider.name, "variants": len(result.variants)}
        return {"ok": False, "provider": provider.name, "error": result.error}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "provider": provider.name, "error": str(exc)}
