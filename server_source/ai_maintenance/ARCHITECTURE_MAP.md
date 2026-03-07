# ARCHITECTURE MAP

## Entry
- `main.py` mounts all routers.

## Core rules
- `core/` contains combat, rewards, leveling, MBTI, promotion, classes, and schemas.

## Transport layer
- `routers/` contains API endpoints grouped by feature.

## Persistence
- `storage/` contains in-memory and SQLite repository logic.

## Quality
- `tests/` contains pytest validation and should remain green after changes.

## Recommended AI reading order
1. `main.py`
2. `routers/`
3. `core/`
4. `storage/`
5. `tests/`
