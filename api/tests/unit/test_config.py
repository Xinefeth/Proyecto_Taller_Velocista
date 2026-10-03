from app.core.config import Settings


def test_url_de_base_de_datos_y_cors():
    s = Settings(
        postgres_user="u",
        postgres_password="p",
        postgres_host="127.0.0.1",
        postgres_port=5432,
        postgres_db="d",
        cors_origins="http://a, http://b",
    )
    assert s.database_url == "postgresql+psycopg://u:p@127.0.0.1:5432/d"
    assert s.cors_list == ["http://a", "http://b"]
