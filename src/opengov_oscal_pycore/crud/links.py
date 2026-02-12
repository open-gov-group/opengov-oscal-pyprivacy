from __future__ import annotations

from typing import Iterable, Optional, List, Sequence

from ..models import Link


def list_links(links: Sequence[Link] | None) -> List[Link]:
    return list(links or [])


def find_links(
    links: Sequence[Link] | None,
    *,
    rel: str | None = None,
    href: str | None = None,
) -> List[Link]:
    """Return all links matching the given filters."""
    out: List[Link] = []
    for l in links or []:
        if rel is not None and l.rel != rel:
            continue
        if href is not None and l.href != href:
            continue
        out.append(l)
    return out


def get_link(
    links: Sequence[Link] | None,
    rel: str,
    *,
    href: str | None = None,
) -> Optional[Link]:
    matches = find_links(links, rel=rel, href=href)
    return matches[0] if matches else None


def upsert_link(
    links: List[Link],
    link: Link,
    *,
    key: Iterable[str] = ("rel", "href"),
) -> Link:
    """Insert or update a Link in-place.

    Default idempotency key is (rel, href). This works well for
    normalized references and avoids duplicates.
    """
    def _k(l: Link) -> tuple:
        return tuple(getattr(l, field) for field in key)

    target_key = _k(link)
    for existing in links:
        if _k(existing) == target_key:
            # update fields (keep same identity key)
            existing.text = link.text
            existing.href = link.href
            existing.rel = link.rel
            return existing

    links.append(link)
    return link


def remove_links(
    links: List[Link],
    *,
    rel: str | None = None,
    href: str | None = None,
) -> None:
    """Remove all links matching the filters."""
    links[:] = [
        l for l in links
        if not (
            (rel is None or l.rel == rel)
            and (href is None or l.href == href)
        )
    ]
