import logging

from celery import shared_task
from opportunity.models import Opportunity

from search.models import Match
from utils.vector_db import retriever_topk

logger = logging.getLogger(__name__)


@shared_task(name="match_proposals")
def match_proposals(pk: int, summary: str) -> None:
    logger.info(f"Matching started for: {summary.split()[:10]}")

    uuids = [doc.metadata["id"] for doc in retriever_topk(k=3, _filter={"funding": True}).invoke(summary)]
    opportunities = [Opportunity.objects.get(pk=uuid) for uuid in uuids]

    matched = []
    for opportunity in opportunities:
        matched.append(
            {
                "id": str(opportunity.id),
                "title": opportunity.title,
                "max_funding": opportunity.funding,
                "categories": parse_categories(categories=opportunity.categories),
                "applications": opportunity.applications,
                "success_rate": opportunity.success_rate,
            }
        )

    Match.objects.filter(pk=pk).update(proposals=matched)


def parse_categories(categories: list[str], limit: int = 20) -> list[str]:
    return [" ".join(category.split("_")) for category in categories if len(category) <= limit]
