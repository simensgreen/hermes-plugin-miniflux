"""Miniflux RSS plugin for Hermes."""
from pathlib import Path

from . import schemas, tools


TOOLSET = "miniflux_rss"


def register(ctx):
    """Register Miniflux tools."""
    ctx.register_skill(
        "miniflux-rss-workflow",
        Path(__file__).parent / "skills" / "miniflux-rss-workflow" / "SKILL.md",
    )
    ctx.register_tool(
        name="miniflux_check",
        schema=schemas.MINIFLUX_CHECK,
        handler=tools.miniflux_check,
        toolset=TOOLSET,
    )
    ctx.register_tool(
        name="miniflux_list_unread_entries",
        schema=schemas.MINIFLUX_LIST_UNREAD_ENTRIES,
        handler=tools.miniflux_list_unread_entries,
        toolset=TOOLSET,
    )
    ctx.register_tool(
        name="miniflux_consume_unread_entries",
        schema=schemas.MINIFLUX_CONSUME_UNREAD_ENTRIES,
        handler=tools.miniflux_consume_unread_entries,
        toolset=TOOLSET,
    )
    ctx.register_tool(
        name="miniflux_mark_entries_read",
        schema=schemas.MINIFLUX_MARK_ENTRIES_READ,
        handler=tools.miniflux_mark_entries_read,
        toolset=TOOLSET,
    )
    ctx.register_tool(
        name="miniflux_list_categories",
        schema=schemas.MINIFLUX_LIST_CATEGORIES,
        handler=tools.miniflux_list_categories,
        toolset=TOOLSET,
    )
    ctx.register_tool(
        name="miniflux_list_feeds",
        schema=schemas.MINIFLUX_LIST_FEEDS,
        handler=tools.miniflux_list_feeds,
        toolset=TOOLSET,
    )
