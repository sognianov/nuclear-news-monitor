import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime, timedelta
import re
import pytz

# --- CONFIG ---

RSS_FEEDS = {
    # Nuclear & Tariffs (existing)
    "Google News - Nuclear Energy": "https://news.google.com/rss/search?q=nuclear+energy",
    "Google News - Tariffs": "https://news.google.com/rss/search?q=tariffs",
    "Google News - Politics": "https://news.google.com/rss/search?q=politics",
    "Google News - Markets": "https://news.google.com/rss/search?q=markets",
    "Google News - Economy": "https://news.google.com/rss/search?q=economy",
    "Google News - Trade": "https://news.google.com/rss/search?q=trade",
    "Google News - Bloomberg": "https://news.google.com/rss/search?q=Bloomberg",
    "Google News - Reuters": "https://news.google.com/rss/search?q=Reuters",
    "Google News - CNBC": "https://news.google.com/rss/search?q=CNBC",
    "Google News - MarketWatch": "https://news.google.com/rss/search?q=MarketWatch",
    "Google News - Financial Times": "https://news.google.com/rss/search?q=Financial+Times",
    "US NRC News": "https://www.nrc.gov/reading-rm/doc-collections/news/rss.xml",
    "DOE Press Office": "https://www.energy.gov/doe-press-office/rss.xml",
    "DOE News": "https://www.energy.gov/articles/rss.xml",
    "EIA News": "https://www.eia.gov/rss/news.xml",
    "Reuters Energy": "https://www.reuters.com/business/energy/rss",
    "Reuters Business": "https://www.reuters.com/rssFeed/businessNews",
    "Reuters Politics": "https://www.reuters.com/politics/rss",
    "Bloomberg Energy": "https://www.bloomberg.com/feeds/podcast/energy-news.xml",
    "Bloomberg Top Stories": "https://www.bloomberg.com/feed/podcast/top-stories.xml",
    "Bloomberg Markets": "https://www.bloomberg.com/feeds/podcast/markets.xml",
    "Bloomberg Politics": "https://www.bloomberg.com/feeds/podcast/politics.xml",
    "CNBC Top News": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "CNBC Markets": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "CNBC Politics": "https://www.cnbc.com/id/10000113/device/rss/rss.html",
    "MarketWatch Top Stories": "https://www.marketwatch.com/rss/topstories",
    "MarketWatch Markets": "https://www.marketwatch.com/rss/markets",
    "MarketWatch Economy": "https://www.marketwatch.com/rss/economy",
    "Financial Times": "https://www.ft.com/?format=rss",
    "Financial Times Markets": "https://www.ft.com/markets/rss",
    "Financial Times Politics": "https://www.ft.com/politics/rss",
    "Washington Post Energy": "https://www.washingtonpost.com/rss/energy-environment/",
    "NPR Energy": "https://www.npr.org/rss/rss.php?id=1017",
    "Bing News - Nuclear Energy": "https://www.bing.com/news/search?q=nuclear+energy&format=rss",
    "Bing News - Politics": "https://www.bing.com/news/search?q=politics&format=rss",
    "Bing News - Markets": "https://www.bing.com/news/search?q=markets&format=rss",
    "Bing News - Economy": "https://www.bing.com/news/search?q=economy&format=rss",
    "Bing News - Trade": "https://www.bing.com/news/search?q=trade&format=rss",
}

KEYWORD_GROUPS = {
    "Executive Order & Trump": ["executive order", "trump"],
    "Tariffs & Trump": ["tariff", "trump"],
    "Trade War": ["trade war"],
    "Levies": ["levies"],
    "Nuclear": ["nuclear"],
    "Uranium": ["uranium"],
    "Fission": ["fission"],
    "Fusion": ["fusion"],
    "DOE": ["doe"],
    "NRC": ["nrc"],
    "Uranium Enrichment": ["uranium enrichment"],
    "Section 232": ["section 232"],
    "Defense Production Act": ["defense production act"],
    "Nuclear Licensing": ["nuclear licensing"],
    "Trade Agreement": ["trade agreement"]
}

# --- TIME ZONE CONFIG ---
cet = pytz.timezone("CET")

# --- HELPER FUNCTIONS ---

def matches_keyword_group(text, keywords):
    text = text.lower()
    return all(re.search(r'\b{}\b'.format(re.escape(kw.lower())), text) for kw in keywords)

def parse_date(date_str):
    for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z']:
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.min

def fetch_articles():
    articles = []
    now = datetime.now(cet)
    day_ago = now - timedelta(days=1)

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        if not feed.entries:
            continue

        for entry in feed.entries:
            title = entry.title
            summary = entry.get("summary", "")
            link = entry.link
            published = entry.get("published", None)
            if not published:
                continue

            published_dt = parse_date(published)
            if published_dt.tzinfo is None:
                published_dt = cet.localize(published_dt)
            else:
                published_dt = published_dt.astimezone(cet)

            if published_dt < day_ago:
                continue

            content = (title + " " + summary).lower()

            matched_group = None
            for group_name, keywords in KEYWORD_GROUPS.items():
                if matches_keyword_group(content, keywords):
                    matched_group = group_name
                    break

            if matched_group:
                articles.append({
                    "Title": title,
                    "Summary": summary,
                    "Link": link,
                    "Published": published_dt,
                    "Source": source,
                    "Keyword Group": matched_group
                })

    articles.sort(key=lambda x: x["Published"], reverse=True)
    return articles

# --- STREAMLIT DASHBOARD ---

st.set_page_config(page_title="Nuclear & Tariff Monitor", layout="wide")
st.title("🔍 Nuclear & Tariff Executive Order Monitor")
st.write("Tracking focused keywords in real time from major energy & government news sources (last 24 hours).")

if st.button("Run"):
    with st.spinner("Collecting data..."):
        data = fetch_articles()
        df = pd.DataFrame(data)

        if df.empty:
            st.warning("No matching articles found in the past 24 hours.")
            st.stop()

        st.sidebar.header("Filter Articles")

        sources = list(df['Source'].unique())
        selected_sources = st.sidebar.multiselect("Select Sources", sources, default=sources)

        keyword_groups = list(KEYWORD_GROUPS.keys())
        selected_keywords = st.sidebar.multiselect("Select Keyword Groups", keyword_groups, default=keyword_groups)

        min_date = df['Published'].min().date()
        max_date = df['Published'].max().date()
        selected_dates = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

        filtered_df = df[
            (df['Source'].isin(selected_sources)) &
            (df['Keyword Group'].isin(selected_keywords)) &
            (df['Published'].dt.date >= selected_dates[0]) &
            (df['Published'].dt.date <= selected_dates[1])
        ]

        st.subheader("Article Hits by Source")
        st.table(filtered_df['Source'].value_counts())

        def make_clickable(url):
            return f'<a href="{url}" target="_blank">Link</a>'

        filtered_display = filtered_df[['Published', 'Title', 'Source', 'Keyword Group', 'Link']].copy()
        filtered_display['Link'] = filtered_display['Link'].apply(make_clickable)

        st.markdown(
            filtered_display.to_html(escape=False, index=False),
            unsafe_allow_html=True,
        )
else:
    st.info("Click 'Run' to collect and filter articles.")
