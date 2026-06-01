from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class AppwriteOuraConfig:
    endpoint: str
    project_id: str
    database_id: str
    collection_id: str
    user_id: str
    api_key: str
    page_size: int = 100


def _build_queries(page_size: int, user_id: str, cursor_after: str | None) -> list[str]:
    queries = [
        f'limit({page_size})',
        f'equal("userId", ["{user_id}"])',
    ]
    if cursor_after:
        queries.append(f'cursorAfter("{cursor_after}")')
    return queries


def _build_params(queries: list[str]) -> list[tuple[str, str]]:
    return [("queries[]", query) for query in queries]


def fetch_all_oura_documents(config: AppwriteOuraConfig) -> list[dict[str, Any]]:
    endpoint = config.endpoint.rstrip("/")
    url = (
        f"{endpoint}/databases/{config.database_id}/"
        f"collections/{config.collection_id}/documents"
    )
    headers = {
        "X-Appwrite-Project": config.project_id,
        "X-Appwrite-Key": config.api_key,
        "Content-Type": "application/json",
    }

    all_docs: list[dict[str, Any]] = []
    cursor_after: str | None = None

    while True:
        params = _build_params(
            _build_queries(
                page_size=config.page_size,
                user_id=config.user_id,
                cursor_after=cursor_after,
            )
        )
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        payload = response.json()
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError("Invalid Appwrite response: 'documents' is not a list")

        if not documents:
            break

        all_docs.extend(documents)
        cursor_after = documents[-1].get("$id")
        if len(documents) < config.page_size or not cursor_after:
            break

    return all_docs
