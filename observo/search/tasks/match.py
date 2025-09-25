import logging

from celery import shared_task
from opportunity.models import Opportunity

from search.models import Match
from utils.vector_db import retriever_topk

logger = logging.getLogger(__name__)


@shared_task(name="match_proposals")
def match_proposals(pk: int, summary: str) -> None:
    logger.info(f"Matching started for: {summary.split()[:10]}")

    uuids = [doc.metadata["id"] for doc in retriever_topk(k=3).invoke(summary)]
    opportunities = [Opportunity.objects.get(pk=uuid) for uuid in uuids]

    matched = []
    for opportunity in opportunities:
        matched.append(
            {
                "title": opportunity.title,
                "max_funding": opportunity.funding,
                "deadline": opportunity.closed.strftime("%Y/%m/%d") if opportunity.closed else None,
                "applications": 10,
                "success_rate": 10,
            }
        )

    Match.objects.filter(pk=pk).update(proposals=matched)
