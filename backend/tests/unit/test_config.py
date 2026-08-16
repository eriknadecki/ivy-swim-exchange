from app.config import Settings


def test_plain_postgres_url_gets_psycopg_driver() -> None:
    s = Settings(database_url="postgres://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_postgresql_url_gets_psycopg_driver() -> None:
    s = Settings(database_url="postgresql://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_already_qualified_url_is_left_alone() -> None:
    s = Settings(database_url="postgresql+psycopg://user:pw@host:5432/db")
    assert s.database_url == "postgresql+psycopg://user:pw@host:5432/db"


def test_cors_origins_accepts_comma_separated_string() -> None:
    s = Settings(cors_allow_origins="https://a.example.com, https://b.example.com")
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_accepts_json_array_string() -> None:
    s = Settings(cors_allow_origins='["https://a.example.com","https://b.example.com"]')
    assert s.cors_allow_origins == ["https://a.example.com", "https://b.example.com"]


def test_cors_origins_default() -> None:
    s = Settings()
    assert "http://localhost:5173" in s.cors_allow_origins
