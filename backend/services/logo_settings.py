"""
Thin helper around the `system_settings` table for Logo provider config.

We store ONE row with key='logo_provider_config' whose value is a JSON blob:

    {
      "provider":           "openai" | "ideogram" | "recraft",
      "fallback":           "openai",
      "openai_api_key":     "sk-...",
      "openai_model":       "dall-e-3",
      "ideogram_api_key":   "...",
      "ideogram_model":     "V_3",
      "recraft_api_key":    "...",
      "recraft_model":      "fal-ai/recraft/v4/text-to-vector",
      "style":              "modern",
      "include_text":       true,
      "variant_count":      3,
      "remove_background":  true
    }
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

SETTING_KEY = "logo_provider_config"

# Defaults used when the row doesn't exist yet. Env vars still act as a
# deployment-time override so existing installs keep working.
DEFAULTS: Dict[str, Any] = {
    "provider":           os.getenv("LOGO_PROVIDER", "openai"),
    "fallback":           os.getenv("LOGO_FALLBACK", "openai"),
    "openai_api_key":     os.getenv("LOGO_OPENAI_API_KEY", ""),
    "openai_model":       os.getenv("LOGO_OPENAI_MODEL", "dall-e-3"),
    "ideogram_api_key":   os.getenv("IDEOGRAM_API_KEY", ""),
    "ideogram_model":     os.getenv("IDEOGRAM_MODEL", "V_3"),
    "recraft_api_key":    os.getenv("RECRAFT_API_KEY", ""),
    "recraft_model":      os.getenv("RECRAFT_MODEL", "fal-ai/recraft/v4/text-to-vector"),
    "style":              os.getenv("LOGO_STYLE", "modern"),
    "include_text":       os.getenv("LOGO_INCLUDE_TEXT", "true").lower() == "true",
    "variant_count":      int(os.getenv("LOGO_VARIANT_COUNT", "3")),
    "remove_background":  os.getenv("LOGO_REMOVE_BG", "true").lower() == "true",
}

_API_KEY_FIELDS = ("openai_api_key", "ideogram_api_key", "recraft_api_key")


def load_config(db: Optional[Session]) -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    if db is None:
        return cfg
    try:
        from models import SystemSetting
        row = db.query(SystemSetting).filter(SystemSetting.key == SETTING_KEY).first()
        if row and row.value:
            cfg.update(json.loads(row.value))
    except Exception as exc:                           # noqa: BLE001
        print(f"[logo_settings] load failed, using defaults: {exc}")
    return cfg


def save_config(db: Session, patch: Dict[str, Any]) -> Dict[str, Any]:
    from models import SystemSetting
    current = load_config(db)
    current.update({k: v for k, v in patch.items() if v is not None})
    row = db.query(SystemSetting).filter(SystemSetting.key == SETTING_KEY).first()
    if row:
        row.value = json.dumps(current)
    else:
        row = SystemSetting(key=SETTING_KEY, value=json.dumps(current))
        db.add(row)
    db.commit()
    return current


def redact(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy safe to expose to the frontend (masks all API keys)."""
    out = dict(cfg)
    for field in _API_KEY_FIELDS:
        k = out.get(field) or ""
        if k:
            out[field] = f"{k[:4]}...{k[-4:]}" if len(k) > 8 else "****"
            out[f"{field}_set"] = True
        else:
            out[field] = ""
            out[f"{field}_set"] = False
    return out
