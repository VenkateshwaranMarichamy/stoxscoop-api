"""Compatibility import: use the v1 batch model (full `stoxscoop.event_batches` columns)."""

from app.models.v1 import StoxEventBatch as EventBatch

__all__ = ["EventBatch"]
