import logging

from opensearchpy import OpenSearch

from app.core.config import settings

logger = logging.getLogger(__name__)

def get_opensearch_client() -> OpenSearch:
    kwargs = {
        "hosts": [settings.OPENSEARCH_URI],
        "use_ssl": False,
        "verify_certs": False,
    }
    if settings.OPENSEARCH_USERNAME and settings.OPENSEARCH_PASSWORD:
        kwargs["http_auth"] = (settings.OPENSEARCH_USERNAME, settings.OPENSEARCH_PASSWORD)
    elif settings.ULPF_MODE == "dev":
        kwargs["http_auth"] = ("admin", "StrongPassword123!")

    return OpenSearch(**kwargs)

def index_event(client: OpenSearch, event_dict: dict, index_name="ulpf-events"):
    try:
        client.index(
            index=index_name,
            body=event_dict,
            id=event_dict.get("trace_id", None)
        )
    except Exception as e:
        logger.warning(f"Failed to index event to OpenSearch: {e}")
