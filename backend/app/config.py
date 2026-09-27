import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "skillsprint_ai")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

    ENV: str = os.getenv("ENV", "development")

    # Business rule: policy precedence (highest first)
    POLICY_PRECEDENCE = [
        "Latest Approved Policy",
        "Department SOP",
        "FAQ",
        "Informal Guidance",
    ]

    MANDATORY_COVERAGE_TARGET = 100.0
    TRACEABILITY_TARGET = 100.0
    MAX_GENAI_RETRIES = 3


settings = Settings()
