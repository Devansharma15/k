from __future__ import annotations

import hashlib
import hmac
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any
from uuid import uuid4


class IntegrationConfigError(RuntimeError):
    pass


class IntegrationAuthError(RuntimeError):
    pass


class IntegrationRateLimitError(RuntimeError):
    pass


def _slugify(value: str) -> str:
    slug = []
    for char in value.lower():
        if char.isalnum():
            slug.append(char)
        elif slug and slug[-1] != "-":
            slug.append("-")
    return "".join(slug).strip("-")


def _logo_text(name: str) -> str:
    filtered = [
        chunk
        for chunk in name.replace("(", "").replace(")", "").replace(".", "").split()
        if chunk.lower() not in {"ai", "api", "business"}
    ]
    if not filtered:
        return name[:2].upper()
    if len(filtered) == 1:
        return filtered[0][:2].upper()
    return f"{filtered[0][0]}{filtered[1][0]}".upper()


def _provider(
    name: str,
    connection_type: str,
    accent: str,
    env_keys: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "slug": _slugify(name),
        "type": connection_type,
        "logo": _logo_text(name),
        "accent": accent,
        "env_keys": env_keys or [],
    }


INTEGRATION_CATALOG = [
    {
        "id": "ai-llm-providers",
        "name": "AI / LLM Providers",
        "providers": [
            _provider("OpenAI", "api_key", "#10A37F", ["OPENAI_API_KEY"]),
            _provider("Anthropic", "api_key", "#D4A373", ["ANTHROPIC_API_KEY"]),
            _provider("Google", "api_key", "#4285F4", ["GOOGLE_API_KEY", "GEMINI_API_KEY"]),
            _provider("Mistral AI", "api_key", "#FF7000", ["MISTRAL_API_KEY"]),
            _provider("Cohere", "api_key", "#3951B2", ["COHERE_API_KEY"]),
            _provider("Groq", "api_key", "#F55036", ["GROQ_API_KEY"]),
            _provider("Perplexity AI", "api_key", "#18A0FB", ["PERPLEXITY_API_KEY"]),
            _provider("Replicate", "api_key", "#6D28D9", ["REPLICATE_API_TOKEN", "REPLICATE_API_KEY"]),
            _provider("Hugging Face", "api_key", "#FFCC4D", ["HUGGINGFACEHUB_API_TOKEN", "HUGGINGFACE_API_KEY", "HF_TOKEN"]),
            _provider("Together AI", "api_key", "#06B6D4", ["TOGETHER_API_KEY"]),
        ],
    },
    {
        "id": "communication-messaging",
        "name": "Communication & Messaging",
        "providers": [
            _provider("Slack", "oauth", "#4A154B"),
            _provider("Discord", "oauth", "#5865F2"),
            _provider("Telegram", "api_key", "#229ED9", ["TELEGRAM_BOT_TOKEN", "TELEGRAM_API_KEY"]),
            _provider("WhatsApp Business API", "api_key", "#25D366", ["WHATSAPP_API_KEY", "WHATSAPP_ACCESS_TOKEN"]),
            _provider("Gmail", "oauth", "#EA4335"),
            _provider("Microsoft Teams", "oauth", "#635BFF"),
            _provider("Twilio", "api_key", "#F22F46", ["TWILIO_AUTH_TOKEN", "TWILIO_API_KEY"]),
            _provider("SendGrid", "api_key", "#00AEEF", ["SENDGRID_API_KEY"]),
            _provider("Mailchimp", "api_key", "#FFE01B", ["MAILCHIMP_API_KEY"]),
            _provider("Intercom", "oauth", "#1F8DED"),
        ],
    },
    {
        "id": "crm-sales",
        "name": "CRM & Sales",
        "providers": [
            _provider("HubSpot", "oauth", "#FF7A59"),
            _provider("Salesforce", "oauth", "#00A1E0"),
            _provider("Pipedrive", "oauth", "#176A3A"),
            _provider("Zoho CRM", "oauth", "#E42527"),
            _provider("Freshsales", "oauth", "#0EA5E9"),
            _provider("Close", "api_key", "#111827", ["CLOSE_API_KEY"]),
            _provider("Apollo.io", "api_key", "#6D28D9", ["APOLLO_API_KEY"]),
            _provider("Lemlist", "api_key", "#F97316", ["LEMLIST_API_KEY"]),
            _provider("Outreach", "api_key", "#2563EB", ["OUTREACH_API_KEY"]),
            _provider("monday.com", "oauth", "#F43F5E"),
        ],
    },
    {
        "id": "databases-storage",
        "name": "Databases & Storage",
        "providers": [
            _provider("PostgreSQL", "api_key", "#336791", ["DATABASE_URL", "POSTGRES_URL", "POSTGRES_CONNECTION_STRING"]),
            _provider("MongoDB", "api_key", "#13AA52", ["MONGODB_URI", "MONGO_URL"]),
            _provider("Redis", "api_key", "#DC382D", ["REDIS_URL"]),
            _provider("Supabase", "api_key", "#3ECF8E", ["SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_URL"]),
            _provider("PlanetScale", "api_key", "#000000", ["PLANETSCALE_DATABASE_URL", "DATABASE_URL"]),
            _provider("Firebase", "api_key", "#FFCA28", ["FIREBASE_API_KEY"]),
            _provider("Airtable", "api_key", "#18BFFF", ["AIRTABLE_API_KEY", "AIRTABLE_PAT"]),
            _provider("Pinecone", "api_key", "#0F172A", ["PINECONE_API_KEY"]),
            _provider("Weaviate", "api_key", "#00C2FF", ["WEAVIATE_API_KEY"]),
            _provider("Qdrant", "api_key", "#EF4444", ["QDRANT_API_KEY"]),
        ],
    },
    {
        "id": "productivity-project-management",
        "name": "Productivity & Project Management",
        "providers": [
            _provider("Notion", "oauth", "#111111"),
            _provider("Google Sheets", "oauth", "#34A853"),
            _provider("Trello", "oauth", "#0052CC"),
            _provider("Linear", "oauth", "#5E6AD2"),
            _provider("Asana", "oauth", "#F06A6A"),
            _provider("Jira", "oauth", "#0052CC"),
            _provider("ClickUp", "oauth", "#7B68EE"),
            _provider("Basecamp", "oauth", "#1DCC5D"),
            _provider("Todoist", "oauth", "#E44332"),
            _provider("Microsoft Excel", "oauth", "#217346"),
        ],
    },
    {
        "id": "developer-devops",
        "name": "Developer & DevOps",
        "providers": [
            _provider("GitHub", "oauth", "#24292F"),
            _provider("GitLab", "oauth", "#FC6D26"),
            _provider("Bitbucket", "oauth", "#2684FF"),
            _provider("CircleCI", "oauth", "#161616"),
            _provider("Jenkins", "oauth", "#D24939"),
            _provider("PagerDuty", "oauth", "#06AC38"),
            _provider("Datadog", "oauth", "#632CA6"),
            _provider("Sentry", "oauth", "#362D59"),
            _provider("Vercel", "oauth", "#000000"),
            _provider("Docker", "api_key", "#2496ED", ["DOCKER_API_KEY", "DOCKER_TOKEN"]),
        ],
    },
    {
        "id": "payments-finance",
        "name": "Payments & Finance",
        "providers": [
            _provider("Stripe", "api_key", "#635BFF", ["STRIPE_SECRET_KEY"]),
            _provider("PayPal", "oauth", "#003087"),
            _provider("Razorpay", "api_key", "#072654", ["RAZORPAY_KEY_SECRET", "RAZORPAY_API_KEY"]),
            _provider("Braintree", "api_key", "#000000", ["BRAINTREE_PRIVATE_KEY"]),
            _provider("Paddle", "api_key", "#0EA5E9", ["PADDLE_API_KEY"]),
            _provider("Chargebee", "api_key", "#F59E0B", ["CHARGEBEE_API_KEY"]),
            _provider("QuickBooks", "oauth", "#2CA01C"),
            _provider("Xero", "oauth", "#13B5EA"),
            _provider("Plaid", "api_key", "#111827", ["PLAID_SECRET"]),
            _provider("Wise", "api_key", "#00B9FF", ["WISE_API_KEY"]),
        ],
    },
    {
        "id": "cloud-infrastructure",
        "name": "Cloud & Infrastructure",
        "providers": [
            _provider("Amazon Web Services", "api_key", "#FF9900", ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]),
            _provider("Google Cloud", "api_key", "#4285F4", ["GOOGLE_CLOUD_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"]),
            _provider("Microsoft Azure", "api_key", "#0078D4", ["AZURE_OPENAI_API_KEY", "AZURE_API_KEY"]),
            _provider("Cloudflare", "api_key", "#F38020", ["CLOUDFLARE_API_TOKEN", "CLOUDFLARE_API_KEY"]),
            _provider("Backblaze", "api_key", "#E21E2B", ["BACKBLAZE_APPLICATION_KEY"]),
            _provider("Cloudinary", "api_key", "#3448C5", ["CLOUDINARY_URL", "CLOUDINARY_API_SECRET"]),
            _provider("Imgix", "api_key", "#7C3AED", ["IMGIX_API_KEY"]),
            _provider("Uploadcare", "api_key", "#0EA5E9", ["UPLOADCARE_SECRET_KEY"]),
            _provider("Supabase", "api_key", "#3ECF8E", ["SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_URL"]),
            _provider("Vercel", "oauth", "#000000"),
        ],
    },
    {
        "id": "e-commerce",
        "name": "E-commerce",
        "providers": [
            _provider("Shopify", "oauth", "#95BF47"),
            _provider("WooCommerce", "api_key", "#96588A", ["WOOCOMMERCE_CONSUMER_SECRET"]),
            _provider("BigCommerce", "oauth", "#121118"),
            _provider("Magento", "api_key", "#F26322", ["MAGENTO_API_KEY"]),
            _provider("Wix", "oauth", "#0C6EFC"),
            _provider("Etsy", "oauth", "#F16521"),
            _provider("Amazon", "oauth", "#FF9900"),
            _provider("eBay", "oauth", "#E53238"),
            _provider("Gumroad", "api_key", "#FF90E8", ["GUMROAD_ACCESS_TOKEN"]),
            _provider("Lemon Squeezy", "api_key", "#F59E0B", ["LEMON_SQUEEZY_API_KEY"]),
        ],
    },
    {
        "id": "marketing-analytics",
        "name": "Marketing & Analytics",
        "providers": [
            _provider("Google Analytics", "oauth", "#F9AB00"),
            _provider("Mixpanel", "api_key", "#7856FF", ["MIXPANEL_API_SECRET", "MIXPANEL_TOKEN"]),
            _provider("Amplitude", "api_key", "#2563EB", ["AMPLITUDE_API_KEY"]),
            _provider("Segment", "api_key", "#1F2937", ["SEGMENT_WRITE_KEY"]),
            _provider("PostHog", "api_key", "#F54E00", ["POSTHOG_API_KEY"]),
            _provider("Hotjar", "api_key", "#FF3C00", ["HOTJAR_API_KEY"]),
            _provider("Klaviyo", "api_key", "#111827", ["KLAVIYO_API_KEY"]),
            _provider("ActiveCampaign", "api_key", "#356AE6", ["ACTIVECAMPAIGN_API_KEY"]),
            _provider("Brevo", "api_key", "#0EA5E9", ["BREVO_API_KEY", "SENDINBLUE_API_KEY"]),
            _provider("Iterable", "api_key", "#4F46E5", ["ITERABLE_API_KEY"]),
        ],
    },
    {
        "id": "customer-support",
        "name": "Customer Support",
        "providers": [
            _provider("Zendesk", "oauth", "#03363D"),
            _provider("Freshdesk", "api_key", "#0EA5E9", ["FRESHDESK_API_KEY"]),
            _provider("Help Scout", "oauth", "#1292EE"),
            _provider("Crisp", "api_key", "#2563EB", ["CRISP_IDENTIFIER", "CRISP_API_KEY"]),
            _provider("Tidio", "oauth", "#6D28D9"),
            _provider("Gorgias", "oauth", "#111827"),
            _provider("Drift", "oauth", "#00C2A8"),
            _provider("Kustomer", "oauth", "#7C3AED"),
            _provider("Front", "oauth", "#1D4ED8"),
            _provider("Intercom", "oauth", "#1F8DED"),
        ],
    },
]

DEFAULT_USER_ID = "demo-user"
RATE_LIMIT_WINDOW_SECONDS = 10
RATE_LIMIT_MAX_ATTEMPTS = 3

NANGO_PROVIDER_MAP = {
    "slack": "slack",
    "gmail": "google-mail",  # Matched to user screenshot
    "notion": "notion",
    "google-sheets": "google-sheet",  # Matched to user screenshot
    "hubspot": "hubspot",
    "github": "github-getting-started",  # Matched to user screenshot
    "zendesk": "zendesk",
    "intercom": "intercom",
    "linear": "linear",
    "vercel": "vercel",
    "shopify": "shopify",
}


class IntegrationsService:
    def __init__(self) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        repo_root = Path(__file__).resolve().parents[3]
        self._backend_root = backend_root
        self._repo_root = repo_root
        self._db_path = backend_root / "data" / "integrations.sqlite3"
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._catalog_by_slug = {
            provider["slug"]: provider
            for category in INTEGRATION_CATALOG
            for provider in category["providers"]
        }
        self._session_rate_limits: dict[str, list[float]] = {}
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS integration_connections (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    encrypted_secret TEXT,
                    env_key TEXT,
                    connection_ref TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, provider)
                )
                """
            )
            existing_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(integration_connections)")
            }
            if "connection_id" not in existing_columns:
                connection.execute(
                    "ALTER TABLE integration_connections ADD COLUMN connection_id TEXT"
                )
            connection.execute(
                """
                UPDATE integration_connections
                SET connection_id = COALESCE(connection_id, connection_ref)
                """
            )

    def _get_provider(self, provider: str) -> dict[str, Any]:
        slug = _slugify(provider)
        config = self._catalog_by_slug.get(slug)
        if not config:
            raise ValueError(f"Unknown integration provider: {provider}")
        return config

    def _resolve_user_id(self, requested_user_id: str | None = None) -> str:
        if requested_user_id and requested_user_id != DEFAULT_USER_ID:
            raise IntegrationAuthError("You cannot operate on another user's integrations.")
        return DEFAULT_USER_ID

    def _enforce_session_rate_limit(self, user_id: str, provider: str) -> None:
        key = f"{user_id}:{provider}"
        now = time.time()
        bucket = [
            timestamp
            for timestamp in self._session_rate_limits.get(key, [])
            if now - timestamp < RATE_LIMIT_WINDOW_SECONDS
        ]
        if len(bucket) >= RATE_LIMIT_MAX_ATTEMPTS:
            raise IntegrationRateLimitError(
                "Too many connection attempts. Please wait a few seconds and try again."
            )
        bucket.append(now)
        self._session_rate_limits[key] = bucket

    def _load_connections(self, user_id: str) -> dict[str, sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM integration_connections WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        return {row["provider"]: row for row in rows}

    def get_integrations(self, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        user_id = self._resolve_user_id(user_id)
        connections = self._load_connections(user_id)
        categories: list[dict[str, Any]] = []
        connected_count = 0

        for category in INTEGRATION_CATALOG:
            providers: list[dict[str, Any]] = []
            for provider in category["providers"]:
                connection = connections.get(provider["slug"])
                is_connected = bool(connection and connection["status"] == "connected")
                if is_connected:
                    connected_count += 1
                providers.append(
                    {
                        "id": provider["slug"],
                        "name": provider["name"],
                        "slug": provider["slug"],
                        "category": category["name"],
                        "logo": provider["logo"],
                        "accent": provider["accent"],
                        "type": provider["type"],
                        "status": "Connected" if is_connected else "Not Connected",
                        "connection_id": connection["id"] if connection else None,
                        "connection_ref": connection["connection_id"] if connection else None,
                    }
                )
            categories.append(
                {
                    "id": category["id"],
                    "name": category["name"],
                    "providers": providers,
                }
            )

        total = sum(len(category["providers"]) for category in categories)
        return {
            "summary": {
                "total": total,
                "connected": connected_count,
                "disconnected": total - connected_count,
            },
            "categories": categories,
        }

    def has_connection(self, provider: str, user_id: str = DEFAULT_USER_ID) -> bool:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)
        connections = self._load_connections(user_id)
        row = connections.get(provider_config["slug"])
        return bool(row and row["status"] == "connected")

    def detect_env_key(self, provider: str) -> dict[str, Any]:
        provider_config = self._get_provider(provider)
        env_map = self._read_env_sources()
        for key in provider_config["env_keys"]:
            value = env_map.get(key)
            if value:
                return {
                    "provider": provider_config["slug"],
                    "found": True,
                    "env_key": key,
                    "api_key": value,
                    "masked_key": self._mask_secret(value),
                }

        return {
            "provider": provider_config["slug"],
            "found": False,
            "env_key": None,
            "api_key": None,
            "masked_key": None,
        }

    def connect_api_key(self, provider: str, api_key: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)

        encrypted_secret = self._encrypt_secret(api_key)
        connection_id = self._upsert_connection(
            user_id=user_id,
            provider=provider_config["slug"],
            connection_type="api_key",
            status="connected",
            encrypted_secret=encrypted_secret,
            env_key=None,
            nango_connection_id=f"conn-{provider_config['slug']}-{uuid4().hex[:12]}",
        )
        return {
            "connection_id": connection_id,
            "provider": provider_config["slug"],
            "type": "api_key",
            "status": "Connected",
        }

    def save_api_key(self, provider: str, api_key: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        return self.connect_api_key(provider=provider, api_key=api_key, user_id=user_id)

    def connect_oauth(self, provider: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        return self.create_connect_session(provider=provider, user_id=user_id)

    def create_connect_session(self, provider: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)
        self._enforce_session_rate_limit(user_id, provider_config["slug"])
        integration_id = self._get_nango_integration_id(provider_config["slug"])
        response = self._nango_request(
            "POST",
            "/connect/sessions",
            {
                "tags": {
                    "end_user_id": user_id,
                    "provider": provider_config["slug"],
                },
                "end_user": {"id": user_id},
                "allowed_integrations": [integration_id],
            },
        )
        data = response.get("data", {})
        connect_token = (
            data.get("connect_session_token")
            or data.get("token")
            or response.get("connect_session_token")
            or response.get("token")
        )
        connect_link = (
            data.get("connect_link")
            or data.get("link")
            or response.get("connect_link")
            or response.get("link")
        )
        if not connect_token:
            raise IntegrationConfigError("Nango did not return a connect session token.")
        connection_id = self._upsert_connection(
            user_id=user_id,
            provider=provider_config["slug"],
            connection_type="oauth",
            status="pending",
            encrypted_secret=None,
            env_key=None,
            nango_connection_id=None,
        )
        return {
            "connection_id": connection_id,
            "provider": provider_config["slug"],
            "nango_integration_id": integration_id,
            "type": "oauth",
            "status": "Pending",
            "connect_session_token": connect_token,
        }

    def get_connection(self, provider: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any] | None:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)
        connections = self._load_connections(user_id)
        row = connections.get(provider_config["slug"])
        if not row or row["status"] != "connected":
            return None
        return {
            "connection_id": row["id"],
            "provider": provider_config["slug"],
            "type": row["type"],
            "status": "Connected",
            "connection_ref": row["connection_id"],
        }

    def get_connection_status(self, provider: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)
        local_connection = self._load_connections(user_id).get(provider_config["slug"])
        if local_connection and local_connection["type"] == "oauth" and local_connection["status"] == "pending":
            self._refresh_oauth_connection(provider_config["slug"], user_id)
            local_connection = self._load_connections(user_id).get(provider_config["slug"])
        if not local_connection:
            return {
                "provider": provider_config["slug"],
                "status": "not_connected",
                "connection_id": None,
                "connection_ref": None,
            }
        return {
            "provider": provider_config["slug"],
            "status": local_connection["status"],
            "connection_id": local_connection["id"],
            "connection_ref": local_connection["connection_id"],
        }

    def disconnect_integration(self, provider: str, user_id: str = DEFAULT_USER_ID) -> dict[str, Any]:
        user_id = self._resolve_user_id(user_id)
        provider_config = self._get_provider(provider)
        connections = self._load_connections(user_id)
        row = connections.get(provider_config["slug"])
        if row and row["type"] == "oauth" and row["connection_id"]:
            integration_id = self._get_nango_integration_id(provider_config["slug"])
            try:
                self._nango_request(
                    "DELETE",
                    f"/connection/{urllib.parse.quote(str(row['connection_id']))}",
                    query={"provider_config_key": integration_id},
                )
            except IntegrationConfigError:
                pass
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE integration_connections
                SET status = ?, connection_id = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND provider = ?
                """,
                ("revoked", user_id, provider_config["slug"]),
            )
        return {"provider": provider_config["slug"], "disconnected": True}

    def handle_nango_webhook(
        self,
        payload: dict[str, Any],
        signature: str | None,
        raw_body: bytes | None = None,
    ) -> dict[str, Any]:
        self._verify_webhook_signature(signature, payload, raw_body=raw_body)
        webhook_type = str(payload.get("type") or "").lower()
        operation = str(payload.get("operation") or "").lower()
        provider_key = payload.get("providerConfigKey") or payload.get("provider")
        provider_slug = self._provider_slug_from_nango(provider_key) if provider_key else None
        end_user = payload.get("endUser") or {}
        user_id = self._resolve_user_id(end_user.get("endUserId"))

        if webhook_type == "auth" and operation == "creation" and provider_slug:
            status = "connected" if payload.get("success") else "failed"
            self._upsert_connection(
                user_id=user_id,
                provider=provider_slug,
                connection_type="oauth",
                status=status,
                encrypted_secret=None,
                env_key=None,
                nango_connection_id=payload.get("connectionId"),
            )
        elif webhook_type == "connection.updated" and provider_slug:
            raw_status = str(payload.get("status") or "").lower()
            mapped_status = self._normalize_nango_status(raw_status or "connected")
            self._upsert_connection(
                user_id=user_id,
                provider=provider_slug,
                connection_type="oauth",
                status=mapped_status,
                encrypted_secret=None,
                env_key=None,
                nango_connection_id=payload.get("connection_id") or payload.get("connectionId"),
            )
        return {"received": True}

    def _upsert_connection(
        self,
        user_id: str,
        provider: str,
        connection_type: str,
        status: str,
        encrypted_secret: str | None,
        env_key: str | None,
        nango_connection_id: str | None,
    ) -> str:
        existing_id = None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id FROM integration_connections WHERE user_id = ? AND provider = ?",
                (user_id, provider),
            ).fetchone()
            existing_id = row["id"] if row else f"ic_{uuid4().hex}"
            connection.execute(
                """
                INSERT INTO integration_connections (
                    id, user_id, provider, type, status, encrypted_secret, env_key, connection_ref, connection_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, provider) DO UPDATE SET
                    type = excluded.type,
                    status = excluded.status,
                    encrypted_secret = COALESCE(excluded.encrypted_secret, integration_connections.encrypted_secret),
                    env_key = COALESCE(excluded.env_key, integration_connections.env_key),
                    connection_ref = COALESCE(excluded.connection_ref, integration_connections.connection_ref),
                    connection_id = COALESCE(excluded.connection_id, integration_connections.connection_id),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    existing_id,
                    user_id,
                    provider,
                    connection_type,
                    status,
                    encrypted_secret,
                    env_key,
                    nango_connection_id,
                    nango_connection_id,
                ),
            )
        return existing_id

    def _encrypt_secret(self, value: str) -> str:
        key = os.getenv("INTEGRATIONS_ENCRYPTION_KEY")
        if not key:
            raise IntegrationConfigError("INTEGRATIONS_ENCRYPTION_KEY is not configured.")

        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise IntegrationConfigError(
                "cryptography is required for encrypted integration storage."
            ) from exc

        try:
            fernet = Fernet(key.encode("utf-8"))
        except Exception as exc:
            raise IntegrationConfigError(
                "INTEGRATIONS_ENCRYPTION_KEY is invalid. Generate a Fernet-compatible key."
            ) from exc

        return fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def _get_nango_integration_id(self, provider_slug: str) -> str:
        provider_env_name = f"NANGO_INTEGRATION_{provider_slug.upper().replace('-', '_')}"
        return os.getenv(
            provider_env_name,
            NANGO_PROVIDER_MAP.get(provider_slug, provider_slug),
        )

    def _nango_request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        query: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        secret_key = os.getenv("NANGO_SECRET_KEY")
        if not secret_key:
            raise IntegrationConfigError("NANGO_SECRET_KEY is not configured.")
        base_url = os.getenv("NANGO_API_BASE_URL", "https://api.nango.dev").rstrip("/")
        url = f"{base_url}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query, doseq=True)}"
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8") if body is not None else None,
            headers={
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            error_msg = f"Nango request failed ({exc.code}): {detail or exc.reason}"
            
            # Enrich error message for common Nango configuration issues
            if "Integration does not exist" in error_msg:
                # Try to extract the attempted ID from the body if this was a session creation
                missing_id = None
                if body and "allowed_integrations" in body and body["allowed_integrations"]:
                    missing_id = body["allowed_integrations"][0]
                
                instruction = (
                    f"\n\nFIX: Go to your Nango Dashboard (app.nango.dev), add the integration, "
                    f"and ensure the 'Unique Key' is set to '{missing_id}'."
                    if missing_id else
                    "\n\nFIX: Ensure you have created the matching integration in your Nango Dashboard."
                )
                error_msg += instruction
                
            raise IntegrationConfigError(error_msg) from exc
        except urllib.error.URLError as exc:
            raise IntegrationConfigError("Could not reach Nango API.") from exc
        return json.loads(payload) if payload else {}

    def _load_nango_connections(self, user_id: str) -> dict[str, dict[str, Any]]:
        try:
            response = self._nango_request(
                "GET",
                "/connections",
                query={"tags[end_user_id]": user_id, "limit": "200"},
            )
        except IntegrationConfigError:
            return {}
        mapped: dict[str, dict[str, Any]] = {}
        payload_connections = response.get("connections")
        if not isinstance(payload_connections, list):
            payload_connections = response.get("data", {}).get("connections", [])
        for connection in payload_connections:
            provider = (
                connection.get("provider_config_key")
                or connection.get("provider")
                or connection.get("connection_config")
                or connection.get("connectionConfig")
            )
            if not provider:
                continue
            mapped[self._provider_slug_from_nango(provider)] = connection
        return mapped

    def _refresh_oauth_connection(self, provider: str, user_id: str) -> None:
        oauth_connections = self._load_nango_connections(user_id)
        oauth_connection = oauth_connections.get(provider)
        if not oauth_connection:
            return
        connection_ref = (
            oauth_connection.get("connection_id")
            or oauth_connection.get("id")
            or oauth_connection.get("connectionId")
        )
        self._upsert_connection(
            user_id=user_id,
            provider=provider,
            connection_type="oauth",
            status=self._normalize_nango_status(
                str(oauth_connection.get("status") or "connected")
            ),
            encrypted_secret=None,
            env_key=None,
            nango_connection_id=connection_ref,
        )

    def _provider_slug_from_nango(self, provider_key: str) -> str:
        key_slug = _slugify(provider_key)
        reverse_map = {
            _slugify(nango_key): provider_slug
            for provider_slug, nango_key in NANGO_PROVIDER_MAP.items()
        }
        return reverse_map.get(key_slug, key_slug)

    def _normalize_nango_status(self, status: str) -> str:
        normalized = status.lower()
        if normalized in {"connected", "success", "ok"}:
            return "connected"
        if normalized in {"revoked", "deleted", "disconnected"}:
            return "revoked"
        if normalized in {"failed", "error"}:
            return "failed"
        if normalized in {"pending", "created"}:
            return "pending"
        return normalized or "pending"

    def _verify_webhook_signature(
        self,
        signature: str | None,
        payload: dict[str, Any],
        raw_body: bytes | None = None,
    ) -> None:
        secret = os.getenv("NANGO_WEBHOOK_SECRET") or os.getenv("NANGO_SECRET_KEY")
        if not secret:
            raise IntegrationConfigError("NANGO_SECRET_KEY is not configured.")
        if not signature:
            raise IntegrationAuthError("Missing Nango webhook signature.")
        serialized = raw_body or json.dumps(
            payload,
            separators=(",", ":"),
        ).encode("utf-8")
        expected = hashlib.sha256(secret.encode("utf-8") + serialized).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise IntegrationAuthError("Invalid Nango webhook signature.")

    def _read_env_sources(self) -> dict[str, str]:
        values = dict(os.environ)
        candidate_files = [
            self._repo_root / ".env",
            self._repo_root / ".env.local",
            self._backend_root / ".env",
            self._backend_root / ".env.local",
        ]

        for file_path in candidate_files:
            if file_path.exists():
                values.update(self._parse_env_file(file_path))
        return values

    @staticmethod
    def _parse_env_file(file_path: Path) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for raw_line in file_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip().strip("'\"")
        return parsed

    @staticmethod
    def _mask_secret(secret: str) -> str:
        if len(secret) <= 8:
            return "*" * len(secret)
        return f"{secret[:4]}{'*' * max(4, len(secret) - 8)}{secret[-4:]}"


integrations_service = IntegrationsService()
