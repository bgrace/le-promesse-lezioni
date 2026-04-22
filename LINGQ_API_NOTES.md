# LingQ API notes

Date checked: 2026-04-21

## What looks true

- LingQ still publishes official docs for the legacy v2 REST API only.
- Community reports indicate v2 and v3 are both active and you often need both.
- Third-party tools appear to use v3 mainly for reads and discovery, while still using v2 for some writes.

## Endpoints repeatedly reported by the community

- `GET /api/v3/{language_code}/cards/`
  - Card list, paginated.
- `GET /api/v3/{language_code}/cards/{primary_key}/`
  - Single card detail.
- `GET /api/v3/{language_code}/search/`
  - Library/search results for courses and collections.
- `GET /api/v3/{language_code}/progress/chart_data/?metric=reading&period=today`
  - Progress/statistics example shared on the forum.
- `POST /api/v2/{language_code}/lessons/`
  - Officially documented lesson creation/import.
- `POST /api/v2/{language_code}/lessons/{lesson_id}/resplit/`
  - Officially documented resplit.
- `PATCH /api/v2/{language_code}/cards/{primary_key}/`
  - Community-reported working update path for card status/tags.
- `POST /api/v2/{language_code}/cards/{primary_key}/review/`
  - Community-reported working review endpoint.

## Importing lessons

- The officially documented import path is still `POST /api/v2/{language_code}/lessons/`.
- Forum posts from 2023 also mention `POST /api/v3/{language_code}/lessons/import/` for multipart uploads with audio.
- That v3 import path is not documented by LingQ, so we should treat it as provisional until we verify it against the live web app/network traffic.

## Practical recommendation

1. Start with a cleanroom client that wraps the documented v2 lesson-import endpoint.
2. Treat v3 as an opportunistic layer for reads once we verify exact response shapes.
3. Before implementing any write-heavy automation, capture network traffic from the current LingQ web app and confirm the real lesson import and course-management endpoints in use today.

## Authentication

- Third-party examples consistently use `Authorization: Token <api_key>`.
- LingQ's public docs and third-party tools both point users to the account API key page.
