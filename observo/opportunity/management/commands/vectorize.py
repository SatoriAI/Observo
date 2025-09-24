from django.core.management.base import BaseCommand
from django.db import transaction
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm

from opportunity.models import Opportunity
from opportunity.vector_db import store


class Command(BaseCommand):
    help = "Inject Grants to vector database"

    def add_arguments(self, parser):
        parser.add_argument("--chunk-size", required=False, default=1200)
        parser.add_argument("--chunk-overlap", required=False, default=150)

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        counter = 0
        documents = []

        qs = Opportunity.objects.exclude(vectorized=True)

        for opportunity in tqdm(qs.iterator(), total=qs.count(), unit="grant"):
            documents.append(Document(page_content=opportunity.describe(), metadata={"id": str(opportunity.id)}))
            counter += 1

        chunks = self._chunk(raw=documents, chunk_size=options["chunk_size"], chunk_overlap=options["chunk_overlap"])
        if not chunks:
            self.stdout.write(self.style.NOTICE("No chunks were found!"))
            return

        vector_store = store()
        vector_store.add_documents(chunks)

        qs.update(vectorized=True)
        self.stdout.write(self.style.SUCCESS(f"Successfully injected {counter} Grants (#chunks = {len(chunks)})!"))

    @staticmethod
    def _chunk(raw: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        return splitter.split_documents(list(raw))
