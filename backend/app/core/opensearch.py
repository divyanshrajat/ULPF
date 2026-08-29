from opensearchpy import OpenSearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[settings.OPENSEARCH_URI],
        http_auth=("admin", "StrongPassword123!"),
        use_ssl=False,
        verify_certs=False,
    )

def index_event(client: OpenSearch, event_dict: dict, index_name="ulpf-events"):
    try:
        client.index(
            index=index_name,
            body=event_dict,
            id=event_dict.get("trace_id", None)
        )
    except Exception as e:
        logger.warning(f"Failed to index event to OpenSearch: {e}")
