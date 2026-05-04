"""Tool schemas for the Miniflux RSS Hermes plugin."""

MINIFLUX_CHECK = {
    "name": "miniflux_check",
    "description": (
        "Check that MINIFLUX_URL and MINIFLUX_API_TOKEN are configured and that "
        "the Miniflux API is reachable. Use this before debugging RSS workflows."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
    },
}


MINIFLUX_LIST_UNREAD_ENTRIES = {
    "name": "miniflux_list_unread_entries",
    "description": (
        "List unread Miniflux RSS entries without changing their read status. "
        "Use this for inspection only. For daily news digest workflows, prefer "
        "miniflux_consume_unread_entries so unread entries are marked read after "
        "they are collected."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of unread entries to return. Default 50, max 200.",
                "default": 50,
            },
            "offset": {
                "type": "integer",
                "description": "Result offset for pagination. Default 0.",
                "default": 0,
            },
            "newer_than_hours": {
                "type": "integer",
                "description": (
                    "Optional recency filter by published_at. Example: 24 returns only "
                    "entries published in the last 24 hours."
                ),
            },
            "category_id": {
                "type": "integer",
                "description": (
                    "Optional Miniflux category ID filter. Category IDs are not feed IDs."
                ),
            },
            "feed_id": {
                "type": "integer",
                "description": (
                    "Optional Miniflux feed ID filter. Use only a concrete valid feed ID "
                    "returned by miniflux_list_feeds. Never use feed_id=0. Never pass a "
                    "category ID as feed_id."
                ),
            },
            "include_content": {
                "type": "boolean",
                "description": "Whether to include stripped entry content snippets. Default false.",
                "default": False,
            },
            "max_content_chars": {
                "type": "integer",
                "description": "Maximum stripped content characters per entry when include_content=true. Default 800.",
                "default": 800,
            },
        },
        "required": [],
    },
}


MINIFLUX_CONSUME_UNREAD_ENTRIES = {
    "name": "miniflux_consume_unread_entries",
    "description": (
        "Fetch unread Miniflux RSS entries and then mark exactly those fetched entries "
        "as read. By default this drains matching unread entries across multiple pages "
        "up to max_entries, not just one page. This is the preferred tool for scheduled "
        "news digests: first collect unread RSS events, then deduplicate against "
        "caller context and use web search for topics not covered by RSS. If Miniflux is "
        "unavailable, return an error and continue the digest as if RSS had no entries."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Page size for Miniflux API requests. Default 100, max 200.",
                "default": 100,
            },
            "max_entries": {
                "type": "integer",
                "description": (
                    "Maximum total entries to consume across pages. Default 500, max 2000. "
                    "Use this to avoid token blowups if RSS accumulated a large backlog."
                ),
                "default": 500,
            },
            "drain_all": {
                "type": "boolean",
                "description": (
                    "If true, keep fetching unread entries from the first page and marking "
                    "them read until no matching unread entries remain or max_entries is "
                    "reached. Default true for digest workflows."
                ),
                "default": True,
            },
            "newer_than_hours": {
                "type": "integer",
                "description": (
                    "Optional recency filter by published_at. For daily digest use 24 unless "
                    "the caller needs a different window. Set to 0 or omit only if the "
                    "caller wants to consume the whole unread backlog regardless of age."
                ),
                "default": 24,
            },
            "category_id": {
                "type": "integer",
                "description": (
                    "Optional Miniflux category ID filter. Category IDs are not feed IDs."
                ),
            },
            "feed_id": {
                "type": "integer",
                "description": (
                    "Optional Miniflux feed ID filter. Use only a concrete valid feed ID "
                    "returned by miniflux_list_feeds. Never use feed_id=0. Never pass a "
                    "category ID as feed_id."
                ),
            },
            "include_content": {
                "type": "boolean",
                "description": "Whether to include stripped entry content snippets. Default true.",
                "default": True,
            },
            "max_content_chars": {
                "type": "integer",
                "description": "Maximum stripped content characters per entry. Default 1200.",
                "default": 1200,
            },
        },
        "required": [],
    },
}


MINIFLUX_MARK_ENTRIES_READ = {
    "name": "miniflux_mark_entries_read",
    "description": (
        "Mark specific Miniflux entries as read by ID. This has side effects. "
        "Use it only when the user asked to mark entries read or when a workflow "
        "explicitly says unread RSS entries should be consumed after reading."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "entry_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Miniflux entry IDs to mark as read.",
            },
        },
        "required": ["entry_ids"],
    },
}


MINIFLUX_LIST_CATEGORIES = {
    "name": "miniflux_list_categories",
    "description": (
        "List Miniflux categories with unread counts. Use this to understand RSS "
        "organization or debug why a digest has no RSS entries in a category."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "counts": {
                "type": "boolean",
                "description": "Include feed_count and total_unread if supported by Miniflux. Default true.",
                "default": True,
            },
        },
        "required": [],
    },
}


MINIFLUX_LIST_FEEDS = {
    "name": "miniflux_list_feeds",
    "description": (
        "List Miniflux feeds with their real feed IDs, category metadata, and unread counts "
        "when supported. Use this before filtering by feed_id. Never use feed_id=0; Miniflux "
        "requires a concrete valid feed ID."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": (
                    "Optional feed status filter if supported by Miniflux. Usually omit it. "
                    "This is not entry read/unread status."
                ),
            },
            "category_id": {
                "type": "integer",
                "description": "Optional category ID filter.",
            },
        },
        "required": [],
    },
}
