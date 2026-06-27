from langchain_core.tools import tool
from db.models import SessionLocal, ChannelSnapshot, VideoStats
from sqlalchemy import func, desc
import json


@tool
def get_channel_stats(channel_name: str) -> str:
    """Get the latest subscriber count, total views, and video count for a YouTube channel by name."""
    session = SessionLocal()
    try:
        snapshot = (
            session.query(ChannelSnapshot)
            .filter(ChannelSnapshot.channel_name.ilike(f"%{channel_name}%"))
            .order_by(desc(ChannelSnapshot.fetched_at))
            .first()
        )

        if not snapshot:
            return json.dumps({"error": f"No data found for channel: {channel_name}"})

        return json.dumps({
            "channel_name": snapshot.channel_name,
            "channel_id": snapshot.channel_id,
            "subscriber_count": snapshot.subscriber_count,
            "total_view_count": snapshot.view_count,
            "video_count": snapshot.video_count,
            "data_as_of": snapshot.fetched_at.isoformat(),
        })
    finally:
        session.close()


@tool
def get_top_videos(channel_name: str, limit: int = 5) -> str:
    """Get the top videos for a YouTube channel by name, ranked by view count."""
    session = SessionLocal()
    try:
        videos = (
            session.query(VideoStats)
            .filter(VideoStats.channel_name.ilike(f"%{channel_name}%"))
            .order_by(desc(VideoStats.view_count))
            .limit(limit)
            .all()
        )

        if not videos:
            return json.dumps({"error": f"No video data found for channel: {channel_name}"})

        result = []
        for v in videos:
            result.append({
                "title": v.title,
                "view_count": v.view_count,
                "like_count": v.like_count,
                "comment_count": v.comment_count,
                "engagement_rate_pct": v.engagement_rate,
                "published_at": v.published_at.isoformat() if v.published_at else None,
                "duration_seconds": v.duration_seconds,
            })

        return json.dumps({"channel": channel_name, "top_videos": result})
    finally:
        session.close()


@tool
def compare_channels(channel_name_a: str, channel_name_b: str) -> str:
    """Compare two YouTube channels' subscriber count, total views, video count, and average engagement rate."""
    session = SessionLocal()
    try:
        def get_latest(name: str):
            return (
                session.query(ChannelSnapshot)
                .filter(ChannelSnapshot.channel_name.ilike(f"%{name}%"))
                .order_by(desc(ChannelSnapshot.fetched_at))
                .first()
            )

        def get_avg_engagement(channel_id: str):
            result = (
                session.query(func.avg(VideoStats.engagement_rate))
                .filter(VideoStats.channel_id == channel_id)
                .scalar()
            )
            return round(result, 4) if result else 0.0

        snap_a = get_latest(channel_name_a)
        snap_b = get_latest(channel_name_b)

        if not snap_a:
            return json.dumps({"error": f"No data found for: {channel_name_a}"})
        if not snap_b:
            return json.dumps({"error": f"No data found for: {channel_name_b}"})

        return json.dumps({
            "comparison": {
                snap_a.channel_name: {
                    "subscribers": snap_a.subscriber_count,
                    "total_views": snap_a.view_count,
                    "video_count": snap_a.video_count,
                    "avg_engagement_rate_pct": get_avg_engagement(snap_a.channel_id),
                },
                snap_b.channel_name: {
                    "subscribers": snap_b.subscriber_count,
                    "total_views": snap_b.view_count,
                    "video_count": snap_b.video_count,
                    "avg_engagement_rate_pct": get_avg_engagement(snap_b.channel_id),
                },
            }
        })
    finally:
        session.close()


@tool
def list_tracked_channels(dummy: str = "") -> str:
    """List all YouTube channels currently tracked in the database, with their last data update time."""
    session = SessionLocal()
    try:
        channels = (
            session.query(
                ChannelSnapshot.channel_id,
                ChannelSnapshot.channel_name,
                func.max(ChannelSnapshot.fetched_at).label("last_updated")
            )
            .group_by(ChannelSnapshot.channel_id, ChannelSnapshot.channel_name)
            .all()
        )

        if not channels:
            return json.dumps({"error": "No channels tracked yet. Run the ETL first."})

        return json.dumps({
            "tracked_channels": [
                {
                    "channel_id": c.channel_id,
                    "channel_name": c.channel_name,
                    "last_updated": c.last_updated.isoformat(),
                }
                for c in channels
            ]
        })
    finally:
        session.close()


# Export all tools as a list for the agent
ALL_TOOLS = [get_channel_stats, get_top_videos, compare_channels, list_tracked_channels]