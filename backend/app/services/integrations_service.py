from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4


class IntegrationConfigError(RuntimeError):
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

    def _get_provider(self, provider: str) -> dict[str, Any]:
        slug = _slugify(provider)
        config = self._catalog_by_slug.get(slug)
        if not config:
            raise ValueError(f"Unknown integration provider: {provider}")
        return config

    def _load_connections(self, user_id: str) -> dict[str, sqlite3.Row]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM integration_connections WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        return {row["provider"]: row for row in rows}

    def get_integrations(self, user_id: str = "demo-user") -> dict[str, Any]:
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
                        "connection_ref": connection["connection_ref"] if connection else None,
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

    def detect_env_key(self, provider: str) -> dict[str, Any]:
        provider_config = self._get_provider(provider)
        if provider_config["type"] != "api_key":
            raise ValueError("Env detection is only available for API-key providers.")

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

    def connect_api_key(self, provider: str, api_key: str, user_id: str = "demo-user") -> dict[str, Any]:
        provider_config = self._get_provider(provider)
        if provider_config["type"] != "api_key":
            raise ValueError("This provider requires OAuth, not an API key.")

        encrypted_secret = self._encrypt_secret(api_key)
        connection_id = self._upsert_connection(
            user_id=user_id,
            provider=provider_config["slug"],
            connection_type="api_key",
            status="connected",
            encrypted_secret=encrypted_secret,
            env_key=None,
            connection_ref=f"conn-{provider_config['slug']}-{uuid4().hex[:12]}",
        )
        return {
            "connection_id": connection_id,
            "provider": provider_config["slug"],
            "type": "api_key",
            "status": "Connected",
        }

    def connect_oauth(self, provider: str, user_id: str = "demo-user") -> dict[str, Any]:
        provider_config = self._get_provider(provider)
        if provider_config["type"] != "oauth":
            raise ValueError("This provider expects an API key, not OAuth.")

        auth_url, connection_ref = self._build_nango_auth_url(provider_config["slug"], user_id)
        connection_id = self._upsert_connection(
            user_id=user_id,
            provider=provider_config["slug"],
            connection_type="oauth",
            status="pending",
            encrypted_secret=None,
            env_key=None,
            connection_ref=connection_ref,
        )
        return {
            "connection_id": connection_id,
            "provider": provider_config["slug"],
            "type": "oauth",
            "status": "Pending",
            "auth_url": auth_url,
        }

    def _upsert_connection(
        self,
        user_id: str,
        provider: str,
        connection_type: str,
        status: str,
        encrypted_secret: str | None,
        env_key: str | None,
        connection_ref: str | None,
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
                    id, user_id, provider, type, status, encrypted_secret, env_key, connection_ref
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, provider) DO UPDATE SET
                    type = excluded.type,
                    status = excluded.status,
                    encrypted_secret = COALESCE(excluded.encrypted_secret, integration_connections.encrypted_secret),
                    env_key = COALESCE(excluded.env_key, integration_connections.env_key),
                    connection_ref = COALESCE(excluded.connection_ref, integration_connections.connection_ref),
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
                    connection_ref,
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

    def _build_nango_auth_url(self, provider_slug: str, user_id: str) -> tuple[str, str]:
        base_url = os.getenv("NANGO_BASE_URL")
        public_key = os.getenv("NANGO_PUBLIC_KEY")
        provider_env_name = f"NANGO_PROVIDER_{provider_slug.upper().replace('-', '_')}"
        provider_config_key = os.getenv(provider_env_name)
        success_url = os.getenv("NANGO_SUCCESS_URL")

        if not base_url or not public_key or not provider_config_key:
            raise IntegrationConfigError(
                f"Missing Nango config. Expected NANGO_BASE_URL, NANGO_PUBLIC_KEY, and {provider_env_name}."
            )

        connection_ref = f"{user_id}-{provider_slug}-{uuid4().hex[:10]}"
        auth_url = (
            f"{base_url.rstrip('/')}/oauth/connect?"
            f"public_key={public_key}&provider_config_key={provider_config_key}"
            f"&connection_id={connection_ref}"
        )
        if success_url:
            auth_url = f"{auth_url}&success_url={success_url}"
        return auth_url, connection_ref

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
