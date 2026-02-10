from ldap3 import ALL, SIMPLE, Connection, Server  # type: ignore

from app.security.security import settings


def get_ldap_connection() -> Connection:
    server = Server(
        settings.AD_SERVER,
        port=389,
        use_ssl=False,
        get_info=ALL,
    )

    conn = Connection(
        server,
        user=settings.AD_USERNAME,
        password=settings.AD_PASSWORD,
        authentication=SIMPLE,
        auto_bind=True,
    )

    return conn
