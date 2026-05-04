---
name: miniflux-rss-workflow
description: How to call Miniflux tools for unread RSS (list vs consume, category vs feed IDs, mark-as-read semantics).
version: 0.1.4
metadata:
  hermes:
    tags:
      - rss
      - miniflux
      - news
---

# Miniflux RSS Workflow

Use this skill when the user asks for Miniflux RSS data: unread items, feeds, categories, or consuming unread entries (mark-as-read).

## Category vs feed IDs

Category IDs and feed IDs are different namespaces.

Use `category_id` when filtering by a category.

Use `feed_id` only when filtering by a concrete feed returned by `miniflux_list_feeds`.

Never use `feed_id=0`.

Never convert a category ID into a feed ID.

Example:

```text
Category titled "Example topic" with id 12 -> use category_id=12.
Do not use feed_id=12 for that category unless 12 is a real feed id from list_feeds.
Do not use feed_id=0.
```

## Tool flow

1. Verify config if needed: `miniflux_check`.
2. To list categories or feeds: `miniflux_list_categories`, `miniflux_list_feeds`.
3. If the user asks to read unread entries without marking them read: `miniflux_list_unread_entries`.
4. If the user asks to take unread entries and mark those returned as read: `miniflux_consume_unread_entries`.
5. Pass `category_id` or a valid `feed_id` from step 2 into the entries tools when filtering.
6. Use `newer_than_hours` when the user wants a recency window; use `0` (with `miniflux_consume_unread_entries`) to include the full matching unread backlog regardless of age.
7. Example arguments for draining the unread backlog in one go:

```json
{
  "limit": 100,
  "max_entries": 1000,
  "drain_all": true,
  "newer_than_hours": 0,
  "include_content": true,
  "max_content_chars": 1200
}
```

8. To mark specific entry IDs read without listing first: `miniflux_mark_entries_read` with `entry_ids`.

## Mark-as-read wording

Only say that all unread entries were marked read if the tool result proves it.

Check the tool result:

- `marked_read` must be true.
- `stopped_reason` should be `no_more_unread`.
- `marked_read_count` should match the number of consumed entries.
- If a time/category/feed filter was used, say only that matching entries were marked read.

Do not say "all entries were marked read" if:

- `newer_than_hours` was not `0`.
- `category_id` or `feed_id` was used.
- `stopped_reason` is `max_entries_reached`, `single_page`, `mark_read_failed`, or anything other than `no_more_unread`.
- `mark_read_error` is not null.

Example phrasing:

```text
Marked 20 entries as read that matched the RSS selection.
```

```text
Marked all RSS entries that matched the request as read.
```

```text
Cannot claim every entry was marked read: processing stopped with stopped_reason max_entries_reached.
```

## Failure handling

If Miniflux is unavailable, say that RSS is unavailable and stop RSS-specific processing.
