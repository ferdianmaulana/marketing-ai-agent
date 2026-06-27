import os
import isodate
from dotenv import load_dotenv
from googleapiclient.discovery import build
from datetime import datetime
from db.models import SessionLocal, ChannelSnapshot, VideoStats, init_db, JAKARTA_TZ

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_IDS = [c.strip() for c in os.getenv("YOUTUBE_CHANNEL_IDS", "").split(",") if c.strip()]


def get_youtube_client():
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)


def parse_duration(iso_duration: str) -> int:
    try:
        return int(isodate.parse_duration(iso_duration).total_seconds())
    except Exception:
        return 0


def fetch_channel_stats(youtube, channel_id: str) -> dict:
    response = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    ).execute()

    if not response.get("items"):
        print(f"  Channel {channel_id} not found.")
        return None

    item = response["items"][0]
    stats = item["statistics"]

    return {
        "channel_id": channel_id,
        "channel_name": item["snippet"]["title"],
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
    }


def fetch_top_videos(youtube, channel_id: str, channel_name: str, max_results: int = 10) -> list:
    # Step 1: get video IDs from the channel
    search_response = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        type="video",
        order="viewCount",
        maxResults=max_results
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response.get("items", [])]

    if not video_ids:
        return []

    # Step 2: get detailed stats for those videos
    videos_response = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=",".join(video_ids)
    ).execute()

    videos = []
    for item in videos_response.get("items", []):
        stats = item.get("statistics", {})
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        duration_sec = parse_duration(item["contentDetails"]["duration"])

        engagement = round((likes + comments) / views * 100, 4) if views > 0 else 0.0

        published_at = datetime.fromisoformat(
            item["snippet"]["publishedAt"].replace("Z", "+00:00")
        )

        videos.append({
            "video_id": item["id"],
            "channel_id": channel_id,
            "channel_name": channel_name,
            "title": item["snippet"]["title"],
            "published_at": published_at,
            "view_count": views,
            "like_count": likes,
            "comment_count": comments,
            "duration_seconds": duration_sec,
            "engagement_rate": engagement,
        })

    return videos


def save_channel_snapshot(session, data: dict):
    snapshot = ChannelSnapshot(**data, fetched_at=datetime.now(JAKARTA_TZ))
    session.add(snapshot)


def save_video_stats(session, videos: list):
    for v in videos:
        record = VideoStats(**v, fetched_at=datetime.now(JAKARTA_TZ))
        session.add(record)


def run_etl():
    print(f"[ETL] Starting run at {datetime.now(JAKARTA_TZ).isoformat()}")

    if not CHANNEL_IDS:
        print("[ETL] No channel IDs configured. Check YOUTUBE_CHANNEL_IDS in .env")
        return

    youtube = get_youtube_client()
    session = SessionLocal()

    try:
        for channel_id in CHANNEL_IDS:
            print(f"[ETL] Fetching channel: {channel_id}")

            channel_data = fetch_channel_stats(youtube, channel_id)
            if not channel_data:
                continue

            save_channel_snapshot(session, channel_data)
            print(f"  Channel: {channel_data['channel_name']} | "
                  f"Subscribers: {channel_data['subscriber_count']:,}")

            videos = fetch_top_videos(youtube, channel_id, channel_data["channel_name"])
            save_video_stats(session, videos)
            print(f"  Saved {len(videos)} videos.")

        session.commit()
        print("[ETL] Completed successfully.")

    except Exception as e:
        session.rollback()
        print(f"[ETL] Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
    run_etl()
