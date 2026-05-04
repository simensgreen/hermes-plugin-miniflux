"""Miniflux API handlers for Hermes."""
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request


MAX_LIMIT = 200
DEFAULT_TIMEOUT = 20


def miniflux_check(args: dict, **_kwargs) -> str:
    """Check Miniflux API connectivity."""
    try:
        _ = args or {}
        me = _request_json("GET", "/v1/me")
        return _json({
            "ok": True,
            "configured": True,
            "user": {
                "id": me.get("id"),
                "username": me.get("username"),
                "is_admin": me.get("is_admin"),
                "timezone": me.get("timezone"),
            },
        })
    except Exception as exc:
        return _json(_error(exc))


def miniflux_list_unread_entries(args: dict, **_kwargs) -> str:
    """List unread entries without marking them read."""
    try:
        args = args or {}
        entries_payload = _get_entries(args, status="unread")
        entries = _compact_entries(
            entries_payload.get("entries", []),
            include_content=bool(args.get("include_content", False)),
            max_content_chars=_int_arg(args, "max_content_chars", 800, 0, 5000),
        )
        return _json({
            "ok": True,
            "marked_read": False,
            "total": entries_payload.get("total"),
            "returned": len(entries),
            "entries": entries,
        })
    except Exception as exc:
        return _json(_error(exc))


def miniflux_consume_unread_entries(args: dict, **_kwargs) -> str:
    """Fetch unread entries and mark exactly those entries as read."""
    try:
        args = args or {}
        if "include_content" not in args:
            args = {**args, "include_content": True}
        if "newer_than_hours" not in args:
            args = {**args, "newer_than_hours": 24}
        if "limit" not in args:
            args = {**args, "limit": 100}
        if "max_entries" not in args:
            args = {**args, "max_entries": 500}
        if "drain_all" not in args:
            args = {**args, "drain_all": True}

        raw_entries, mark_result, mark_error, total_initial, page_count, stopped_reason = _consume_unread(args)

        entries = _compact_entries(
            raw_entries,
            include_content=bool(args.get("include_content", True)),
            max_content_chars=_int_arg(args, "max_content_chars", 1200, 0, 8000),
        )
        return _json({
            "ok": True,
            "marked_read": bool(raw_entries) and mark_result.get("ok") is True,
            "marked_read_count": mark_result.get("count", 0),
            "mark_read_error": mark_error,
            "total_unread_matching_query_initial": total_initial,
            "page_count": page_count,
            "stopped_reason": stopped_reason,
            "returned": len(entries),
            "entries": entries,
        })
    except Exception as exc:
        return _json(_error(exc))


def miniflux_mark_entries_read(args: dict, **_kwargs) -> str:
    """Mark specific entries as read."""
    try:
        args = args or {}
        entry_ids = args.get("entry_ids") or []
        if not isinstance(entry_ids, list):
            return _json({"ok": False, "error": "entry_ids must be an array"})
        entry_ids = [int(x) for x in entry_ids if str(x).strip()]
        if not entry_ids:
            return _json({"ok": False, "error": "entry_ids is required"})
        return _json(_mark_entries_read(entry_ids))
    except Exception as exc:
        return _json(_error(exc))


def miniflux_list_categories(args: dict, **_kwargs) -> str:
    """List categories with optional counts."""
    try:
        args = args or {}
        counts = bool(args.get("counts", True))
        payload = _request_json("GET", "/v1/categories", query={"counts": str(counts).lower()})
        categories = []
        for category in payload if isinstance(payload, list) else []:
            categories.append({
                "id": category.get("id"),
                "title": category.get("title"),
                "feed_count": category.get("feed_count"),
                "total_unread": category.get("total_unread"),
                "hide_globally": category.get("hide_globally"),
            })
        return _json({"ok": True, "categories": categories, "count": len(categories)})
    except Exception as exc:
        return _json(_error(exc))


def miniflux_list_feeds(args: dict, **_kwargs) -> str:
    """List feeds and their concrete IDs."""
    try:
        args = args or {}
        query = {}
        if args.get("status") not in (None, ""):
            query["status"] = str(args.get("status"))
        if args.get("category_id") not in (None, ""):
            query["category_id"] = str(int(args.get("category_id")))
        payload = _request_json("GET", "/v1/feeds", query=query or None)
        feeds = []
        for feed in payload if isinstance(payload, list) else []:
            category = feed.get("category") or {}
            feeds.append({
                "id": feed.get("id"),
                "title": feed.get("title"),
                "site_url": feed.get("site_url"),
                "feed_url": feed.get("feed_url"),
                "disabled": feed.get("disabled"),
                "parsing_error_count": feed.get("parsing_error_count"),
                "parsing_error_message": feed.get("parsing_error_message"),
                "checked_at": feed.get("checked_at"),
                "category": {
                    "id": category.get("id"),
                    "title": category.get("title"),
                },
                "hide_globally": feed.get("hide_globally"),
                "total_unread": feed.get("total_unread"),
            })
        return _json({"ok": True, "feeds": feeds, "count": len(feeds)})
    except Exception as exc:
        return _json(_error(exc))


def _get_entries(args: dict, status: str) -> dict:
    limit = _int_arg(args, "limit", 50, 1, MAX_LIMIT)
    offset = _int_arg(args, "offset", 0, 0, 1000000)
    query = {
        "status": status,
        "limit": str(limit),
        "offset": str(offset),
        "order": "published_at",
        "direction": "desc",
    }

    newer_than_hours = args.get("newer_than_hours")
    if newer_than_hours not in (None, "", 0, "0"):
        hours = _int_arg(args, "newer_than_hours", 24, 1, 24 * 365)
        query["published_after"] = str(int(time.time()) - hours * 3600)

    category_id = args.get("category_id")
    feed_id = args.get("feed_id")
    if feed_id not in (None, ""):
        path = f"/v1/feeds/{int(feed_id)}/entries"
    elif category_id not in (None, ""):
        path = f"/v1/categories/{int(category_id)}/entries"
    else:
        path = "/v1/entries"

    return _request_json("GET", path, query=query)


def _consume_unread(args: dict) -> tuple[list[dict], dict, str | None, int | None, int, str]:
    """Consume unread entries safely.

    When marking entries read while paginating, using offset can skip rows because
    the unread result set shrinks. Drain mode therefore repeatedly fetches the
    first page until no matching unread entries remain.
    """
    drain_all = bool(args.get("drain_all", True))
    max_entries = _int_arg(args, "max_entries", 500, 1, 2000)
    page_size = _int_arg(args, "limit", 100, 1, MAX_LIMIT)
    page_args = {**args, "offset": 0}

    all_entries = []
    total_marked = 0
    mark_error = None
    total_initial = None
    page_count = 0
    seen_ids = set()

    while len(all_entries) < max_entries:
        remaining = max_entries - len(all_entries)
        page_args["limit"] = min(page_size, remaining)
        page_args["offset"] = 0

        payload = _get_entries(page_args, status="unread")
        if total_initial is None:
            total_initial = payload.get("total")

        raw_entries = payload.get("entries", [])
        if not raw_entries:
            return all_entries, {"ok": True, "count": total_marked}, mark_error, total_initial, page_count, "no_more_unread"

        page_count += 1
        new_entries = []
        for entry in raw_entries:
            entry_id = entry.get("id")
            if entry_id is None:
                continue
            entry_id = int(entry_id)
            if entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)
            new_entries.append(entry)

        if not new_entries:
            return all_entries, {"ok": True, "count": total_marked}, mark_error, total_initial, page_count, "no_new_ids"

        entry_ids = [int(e["id"]) for e in new_entries if e.get("id") is not None]
        try:
            result = _mark_entries_read(entry_ids)
            total_marked += result.get("count", 0)
        except Exception as exc:
            mark_error = str(exc)
            all_entries.extend(new_entries)
            return all_entries, {"ok": False, "count": total_marked}, mark_error, total_initial, page_count, "mark_read_failed"

        all_entries.extend(new_entries)

        if not drain_all:
            return all_entries, {"ok": True, "count": total_marked}, mark_error, total_initial, page_count, "single_page"

    return all_entries, {"ok": True, "count": total_marked}, mark_error, total_initial, page_count, "max_entries_reached"


def _mark_entries_read(entry_ids: list[int]) -> dict:
    _request_json("PUT", "/v1/entries", body={"entry_ids": entry_ids, "status": "read"}, expected=(200, 201, 204))
    return {"ok": True, "count": len(entry_ids)}


def _request_json(method: str, path: str, query: dict | None = None, body: dict | None = None, expected=(200, 201, 204)):
    base_url, token = _config()
    url = base_url + path
    if query:
        url += "?" + urllib.parse.urlencode(query, doseq=True)

    data = None
    headers = {
        "X-Auth-Token": token,
        "Accept": "application/json",
        "User-Agent": "hermes-plugin-miniflux/0.3.0",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            status = getattr(resp, "status", resp.getcode())
            raw = resp.read()
            if status not in expected:
                raise RuntimeError(f"Miniflux returned HTTP {status}: {raw[:500]!r}")
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Miniflux HTTP {exc.code}: {raw[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Miniflux connection error: {exc.reason}") from exc


def _config() -> tuple[str, str]:
    base_url = (os.getenv("MINIFLUX_URL") or "").strip().rstrip("/")
    token = (os.getenv("MINIFLUX_API_TOKEN") or "").strip()
    if not base_url:
        raise RuntimeError("MINIFLUX_URL is not configured")
    if not token:
        raise RuntimeError("MINIFLUX_API_TOKEN is not configured")
    return base_url, token


def _compact_entries(entries: list[dict], include_content: bool, max_content_chars: int) -> list[dict]:
    compact = []
    for entry in entries:
        feed = entry.get("feed") or {}
        category = feed.get("category") or {}
        item = {
            "id": entry.get("id"),
            "title": entry.get("title"),
            "url": entry.get("url"),
            "comments_url": entry.get("comments_url"),
            "author": entry.get("author"),
            "published_at": entry.get("published_at"),
            "created_at": entry.get("created_at"),
            "changed_at": entry.get("changed_at"),
            "status": entry.get("status"),
            "starred": entry.get("starred"),
            "reading_time": entry.get("reading_time"),
            "feed": {
                "id": feed.get("id"),
                "title": feed.get("title"),
                "site_url": feed.get("site_url"),
            },
            "category": {
                "id": category.get("id"),
                "title": category.get("title"),
            },
        }
        if include_content:
            item["content_text"] = _truncate(_html_to_text(entry.get("content") or ""), max_content_chars)
        compact.append(item)
    return compact


def _html_to_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?i)<br\s*/?>", "\n", value)
    value = re.sub(r"(?i)</p\s*>", "\n", value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s+", "\n", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _truncate(value: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "…"


def _int_arg(args: dict, key: str, default: int, minimum: int, maximum: int) -> int:
    raw = args.get(key, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


def _error(exc: Exception) -> dict:
    return {"ok": False, "error": str(exc), "error_type": exc.__class__.__name__}


def _json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
