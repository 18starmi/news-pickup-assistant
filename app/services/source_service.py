import sqlite3

from app.core.source_catalog import DEFAULT_SOURCE_DEFINITIONS, LEGACY_DEFAULT_SOURCE_NAMES
from app.db.repositories.source_repository import SourceRepository
from app.domain.source import Source


class SourceService:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.source_repository = SourceRepository(connection)

    def sync_default_sources(self) -> list[Source]:
        existing_by_name = {source.name: source for source in self.source_repository.list_all()}
        synced_sources: list[Source] = []
        current_default_names = {definition.name for definition in DEFAULT_SOURCE_DEFINITIONS}

        for definition in DEFAULT_SOURCE_DEFINITIONS:
            existing = existing_by_name.get(definition.name)
            if existing is not None:
                if (
                    existing.base_url != definition.base_url
                    or existing.kind != definition.kind
                    or existing.is_active != definition.is_active
                ):
                    synced_sources.append(
                        self.source_repository.update(
                            Source(
                                id=existing.id,
                                name=definition.name,
                                base_url=definition.base_url,
                                kind=definition.kind,
                                is_active=definition.is_active,
                                created_at=existing.created_at,
                            )
                        )
                    )
                else:
                    synced_sources.append(existing)
                continue

            synced_sources.append(
                self.source_repository.create(
                    Source(
                        id=None,
                        name=definition.name,
                        base_url=definition.base_url,
                        kind=definition.kind,
                        is_active=definition.is_active,
                    )
                )
            )

        for legacy_name in LEGACY_DEFAULT_SOURCE_NAMES - current_default_names:
            existing = existing_by_name.get(legacy_name)
            if existing is not None and existing.is_active:
                self.source_repository.set_active_by_name(legacy_name, False)

        return synced_sources

    def list_sources(self) -> list[Source]:
        return self.source_repository.list_all()

    def list_active_sources(self) -> list[Source]:
        return self.source_repository.list_active()
