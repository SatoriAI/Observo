import logging
from functools import lru_cache
from math import ceil

from celery import shared_task
from langchain_text_splitters import RecursiveCharacterTextSplitter
from opportunity.models import Opportunity

from search.models import Match
from utils.vector_db import store

logger = logging.getLogger(__name__)


@shared_task(name="match_proposals")
def match_proposals(pk: int, summary: str, funding: bool = True, unique_grants: int = 3) -> None:
    logger.info(f"Matching started for: {summary.split()[:10]}")

    avg_chunks_per_doc = get_avg_chunks_per_doc()
    k = min(max(unique_grants * avg_chunks_per_doc * 2, 50), 200)
    logger.debug(f"MMR retrieval params -> k={k}, k={k}, avg_chunks={avg_chunks_per_doc}")

    retriever = store().as_retriever(
        search_type="mmr",
        search_kwargs={"k": k, "fetch_k": k, "lambda_mult": 0.3, "filter": {"funding": funding}},
    )

    docs = retriever.invoke(summary)
    # Also compute scored similarities and keep the best (lowest) distance per opportunity id
    scored = store().similarity_search_with_score(summary, k=k, filter={"funding": funding})
    id_to_distance: dict[str, float] = {}
    for scored_doc, distance in scored:
        gid = scored_doc.metadata.get("id")
        if not gid:
            continue
        if gid not in id_to_distance or distance < id_to_distance[gid]:
            id_to_distance[gid] = distance
    uuids: list[str] = []
    for doc in docs:
        grant_id = doc.metadata.get("id")
        if grant_id and grant_id not in uuids:
            uuids.append(grant_id)
        if len(uuids) == unique_grants:
            break
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
                "distance": id_to_distance.get(str(opportunity.id)),
            }
        )

    Match.objects.filter(pk=pk).update(proposals=matched)


def parse_categories(categories: list[str], limit: int = 20) -> list[str]:
    return [" ".join(category.split("_")) for category in categories if len(category) <= limit]


@lru_cache(maxsize=1)
def get_avg_chunks_per_doc() -> int:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)
    counts = []

    for opp in Opportunity.objects.all().iterator():
        counts.append(len(splitter.split_text(opp.describe())))

    if not counts:
        logger.warning("Average chunks per doc: dataset is empty; defaulting to 4")
        return 4

    return ceil(sum(counts) / len(counts))
