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
days = st.number_input("Enter Days to Search (1-60):", min_value=1, max_value=60, value=30)

# Keywords
keywords = [
    "AI Bigfoot vlog", "Forest AI vlog", "Mythical creature vlog", "AI-generated forest vlog",
    "AI Bigfoot cooking", "Bigfoot forest adventure", "Bigfoot deer hunting AI", "Cryptid comedy vlog",
    "Funny AI Bigfoot", "Bigfoot forest discovery", "AI Bigfoot prank hunters", "Bigfoot BBQ AI",
    "Yeti vs Bigfoot vlog", "Bigfoot woodworking AI", "AI Bigfoot lake swim", "AI Bigfoot yoga session",
    "AI forest workout vlog", "Bigfoot cabin build AI", "AI-generated cryptid vlog", "Bigfoot wildlife vlog",
    "Bigfoot forest prank video", "Bigfoot cooking pizza AI", "AI Bigfoot lost gear", "AI Bigfoot full day vlog",
    "Bigfoot AI companionship"
]

important_keywords = ["ai", "bigfoot", "vlog", "forest", "prank", "funny", "cryptid", "cooking", "hunting", "adventure"]

# Fetch Data Button
if st.button("Fetch Data"):
    try:
        start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
        all_results = []

        for keyword in keywords:
            st.write(f"🔍 Searching for keyword: `{keyword}`")

            search_params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": start_date,
                "maxResults": 25,
                "key": API_KEY,
            }

            response = requests.get(YOUTUBE_SEARCH_URL, params=search_params)
            data = response.json()

            # Debug output
            if "items" not in data:
                st.warning(f"❌ No response for keyword: {keyword}")
                st.json(data)
                continue

            videos = data["items"]
            if not videos:
                st.warning(f"⚠️ No videos found for keyword: {keyword}")
                continue

            video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
            channel_ids = [v["snippet"]["channelId"] for v in videos if "snippet" in v and "channelId" in v["snippet"]]

            if not video_ids or not channel_ids:
                st.warning(f"⚠️ Skipping keyword: {keyword} due to missing video/channel IDs.")
                continue

            stats_response = requests.get(YOUTUBE_VIDEO_URL, params={
                "part": "statistics", "id": ",".join(video_ids), "key": API_KEY
            })
            stats_data = stats_response.json()

            channel_response = requests.get(YOUTUBE_CHANNEL_URL, params={
                "part": "statistics", "id": ",".join(channel_ids), "key": API_KEY
            })
            channel_data = channel_response.json()

            if "items" not in stats_data or not stats_data["items"]:
                st.warning(f"⚠️ No stats found for keyword: {keyword}")
                continue
            if "items" not in channel_data or not channel_data["items"]:
                st.warning(f"⚠️ No channel data found for keyword: {keyword}")
                continue

            for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
                title = video["snippet"].get("title", "N/A")
                description = video["snippet"].get("description", "")[:100]
                video_url = f"https://www.youtube.com/watch?v={video['id']['videoId']}"
                views = int(stat["statistics"].get("viewCount", 0))
                likes = int(stat["statistics"].get("likeCount", 0))
                comments = int(stat["statistics"].get("commentCount", 0))

                try:
                    subs = int(channel["statistics"].get("subscriberCount", 0))
                except:
                    subs = 0  # If subscriberCount is hidden or unavailable

                # Engagement Rate
                engagement_rate = round(((likes + comments) / views) * 100, 2) if views else 0.0
                title_score = sum(1 for word in important_keywords if word.lower() in title.lower())
                smart_score = round((views / (subs + 1)) * (1 + title_score + (engagement_rate / 100)), 2)

                # Subscriber filter removed for debug phase
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

        # Sort and display
        all_results = sorted(all_results, key=lambda x: x["Smart Score"], reverse=True)

        if all_results:
            st.success(f"✅ Found {len(all_results)} results across all keywords!")
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
            st.warning("😕 No results found — try increasing days or removing filters.")

    except Exception as e:
        st.error(f"❗ Error occurred: {str(e)}")
