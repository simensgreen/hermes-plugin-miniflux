# hermes-plugin-miniflux

Hermes plugin for reading unread Miniflux RSS entries and marking them read after consumption.

## Environment

The Hermes container must have:

```yaml
MINIFLUX_URL: ${MINIFLUX_URL}
MINIFLUX_API_TOKEN: ${MINIFLUX_API_TOKEN}
```

## Tools

- `miniflux_check` — verify API access.
- `miniflux_list_unread_entries` — list unread entries without changing status.
- `miniflux_consume_unread_entries` — list unread entries and mark exactly those entries as read.
- `miniflux_mark_entries_read` — mark specific entry IDs as read.
- `miniflux_list_categories` — list Miniflux categories and unread counts.
- `miniflux_list_feeds` — list concrete feed IDs and feed metadata.

## Install path

Copy the plugin into your Hermes plugins directory (see Hermes docs for `HERMES_HOME` / `plugins/` layout in your environment).

## Enable and test

Use the Hermes CLI for your deployment, for example:

```bash
hermes plugins enable hermes-plugin-miniflux
hermes tools list | grep -Ei 'miniflux|rss'
```

Smoke test: invoke `miniflux_check` once the env vars are set.

For a digest workflow: call `miniflux_consume_unread_entries` with the time window you need, then reconcile with your memory layer and web search for gaps RSS did not cover.
