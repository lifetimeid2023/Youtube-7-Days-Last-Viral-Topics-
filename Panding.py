import streamlit as st
import requests
from datetime import datetime, timedelta

# YouTube API Key
API_KEY = "AIzaSyCP3ceNNGB6IZOfFMSgQWQbxz-SLuFgn9k"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# Streamlit App Title
st.title("YouTube Viral Topics Tool (Smart Score Edition)")

# Input Fields
days = st.number_input("Enter Days to Search (1-90):", min_value=1, max_value=90, value=7)

# List of broader keywords
keywords = [
 "tung tung tung sahur", "tung sahur", "tung tung sahur", "tung turng tung sahur", 
"tung tung tung sahur vr", "tung tung tung sahur 360", "tung tung tung sahur vr 360", "tung tung tung sahur meme", "sahur", 
"tung tung tung tung sahur", "tung tung tung sahur funk", "tung tung tung sahur original", "tungtung sahur", 
"tung tung sahur 3d", "tung tung sahur funk", "tung tung sahur song", 
"tungtungtung sahur", "tung tung sahur modu", "tung sahur funk", "tung tung tung sahur 4k", 
"dipssy tung tung sahur"
]

# Keywords for scoring titles
important_keywords = ["ai", "bigfoot", "vlog", "forest", "prank", "funny", "cryptid", "cooking", "hunting", "adventure"]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"Searching for keyword: {keyword}")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 5,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            if "items" not in data or not data["items"]:
                st.warning(f"No videos found for keyword: {keyword}")
                continue

            videos = data["items"]
            video_ids = [video["id"]["videoId"] for video in videos if "id" in video and "videoId" in video["id"]]
            channel_ids = [video["snippet"]["channelId"] for video in videos if "snippet" in video and "channelId" in video["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"Skipping keyword: {keyword} due to missing video/channel data.")
                continue

            stats_params = {"part": "statistics", "id": ",".join(video_ids), "key": API_KEY}
            stats_response = requests.get(YOUTUBE_VIDEO_URL, params=stats_params)
            stats_data = stats_response.json()

            channel_params = {"part": "statistics", "id": ",".join(channel_ids), "key": API_KEY}
            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params=channel_params)
            channel_data = channel_response.json()

            if "items" not in stats_data or not stats_data["items"] or "items" not in channel_data or not channel_data["items"]:
                continue

            # Dictionary mapping for accurate stats
            video_stats_map = {item["id"]: item for item in stats_data["items"]}
            channel_stats_map = {item["id"]: item for item in channel_data["items"]}

            for video in videos:
                video_id = video["id"].get("videoId")
                channel_id = video["snippet"].get("channelId")

                if not video_id or not channel_id:
                    continue

                stat = video_stats_map.get(video_id)
                channel = channel_stats_map.get(channel_id)

                if not stat or not channel:
                    continue

                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:100]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                views = int(stat["statistics"].get("viewCount", 0))
                likes = int(stat["statistics"].get("likeCount", 0))
                comments = int(stat["statistics"].get("commentCount", 0))
                subs = int(channel["statistics"].get("subscriberCount", 0))

                # Engagement Rate
                engagement_rate = round(((likes + comments) / views) * 100, 2) if views else 0.0

                # Title Score
                title_score = sum(1 for word in important_keywords if word.lower() in title.lower())

                # Smart Score
                smart_score = round((views / (subs + 1)) * (1 + title_score + (engagement_rate / 100)), 2)

                if subs < 5000:
                    all_results.append({
                        "Title": title,
                        "Description": description,
                        "URL": video_url,
                        "Views": views,
                        "Subscribers": subs,
                        "Engagement Rate (%)": engagement_rate,
                        "Title Score": title_score,
                        "Smart Score": smart_score
                    })

        # Sort by Smart Score descending
        all_results = sorted(all_results, key=lambda x: x["Smart Score"], reverse=True)

        if all_results:
            st.success(f"Found {len(all_results)} results across all keywords!")
            for result in all_results:
                st.markdown(
                    f"### 📈 **{result['Title']}**\n"
                    f"- 📹 **Views:** {result['Views']}\n"
                    f"- 👥 **Subscribers:** {result['Subscribers']}\n"
                    f"- 💬 **Engagement Rate:** {result['Engagement Rate (%)']}%\n"
                    f"- 🎯 **Title Score:** {result['Title Score']}\n"
                    f"- 🧠 **Smart Score:** {result['Smart Score']}\n"
                    f"- 🔗 [Watch Now]({result['URL']})\n"
                    f"_{result['Description']}..._"
                )
                st.write("---")
        else:
            st.warning("No results found for channels with fewer than 5,000 subscribers.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
