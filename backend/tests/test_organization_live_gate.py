import pytest

from app.extraction.organization_extraction import extract_chunk
from app.extraction.organization_scheduler import SchedulerHold


def test_live_dispatch_is_rejected_before_claim():
    with pytest.raises(SchedulerHold, match="frozen Stage A"):
        extract_chunk(None, "unapproved", None, [], "document", {})
