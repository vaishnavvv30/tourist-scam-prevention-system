"""
Management command to build/rebuild the RAG vector index.
Usage: python manage.py build_rag_index [--force]
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Build or rebuild the RAG pricing intelligence vector index'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rebuild even if index exists and is current',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Building RAG index...'))

        try:
            from rag_engine.knowledge_base import PRICING_KNOWLEDGE
            self.stdout.write(f'Knowledge base contains {len(PRICING_KNOWLEDGE)} pricing records')

            from rag_engine.services import build_index
            index = build_index(force=options['force'])

            if index:
                self.stdout.write(self.style.SUCCESS(
                    f'RAG index built successfully with {len(PRICING_KNOWLEDGE)} documents!'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    'Failed to build RAG index. Check that required packages are installed:\n'
                    '  pip install llama-index-core llama-index-embeddings-huggingface sentence-transformers faiss-cpu'
                ))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'Missing dependency: {e}'))
            self.stdout.write(self.style.WARNING(
                'Install required packages:\n'
                '  pip install llama-index-core llama-index-embeddings-huggingface sentence-transformers faiss-cpu'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error building index: {e}'))
