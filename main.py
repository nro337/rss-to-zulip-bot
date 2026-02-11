import os
import time
import zulip
import re
import feedparser
import markdownify

# Define your Zulip credentials
ZULIP_EMAIL = os.environ.get("ZULIP_EMAIL")
ZULIP_STREAM_NAME = "rss"

# Define the dictionary of feed names and their RSS links
RSS_FEEDS = {
    "HN": "https://news.ycombinator.com/rss",
    # "arXiv OA and FA": "https://rss.arxiv.org/atom/math.OA+math.FA", doesn't have published_parsed data
    # "Dan Ma's Topology Blog": "https://dantopology.wordpress.com/feed/",
    # "Orr Shalit": "https://noncommutativeanalysis.wordpress.com/feed/",
    # "Free Probability Theory": "https://rolandspeicher.com/feed/",
    # "The Higher Geometer": "https://thehighergeometer.wordpress.com/feed/",
    # "Terence Tao": "https://terrytao.wordpress.com/feed/",
    # "Peter Woit": "https://www.math.columbia.edu/~woit/wordpress/atom.xml",
    # "Math3ma": "http://www.math3ma.com/blog/rss.xml",
    # "Math ∩ Programming": "https://www.jeremykun.com/index.xml",
    # "Ramis Movassagh": "https://ramismovassagh.wordpress.com/blog/feed/",
    # "DESVL": "https://desvl.xyz/atom.xml",
    # "George Lowther": "https://almostsuremath.com/feed",
    # "n-Category Cafe": "https://golem.ph.utexas.edu/category/atom10.xml",
    # "Mathematics, Quanta Magazine": "https://api.quantamagazine.org/mathematics/feed",
    # "Physics, Quanta Magazine": "https://api.quantamagazine.org/physics/feed",
    # "Biology, Quanta Magazine": "https://api.quantamagazine.org/biology/feed",
    # "Computer Science, Quanta Magazine": "https://api.quantamagazine.org/computer-science/feed",
    # "Steven Wolfram, Writings": "https://writings.stephenwolfram.com/feed",
    # "Bit Player": "http://bit-player.org/feed",
    # "Geoff Boeing": "https://geoffboeing.com/feed/",
    # "Azimuth": "https://johncarlosbaez.wordpress.com/feed",
    # "Arch Linux": "https://archlinux.org/feeds/news/",
}

# Function to send a message to Zulip


def send_zulip_message(content, topic):
    client = zulip.Client(email=ZULIP_EMAIL, client="rss-feed-bot/0.1")
    data = {
        "type": "stream",
        "to": ZULIP_STREAM_NAME,
        "topic": topic,
        "content": content,
    }
    client.send_message(data)


# Get the url of the last article update sent to the stream


def last_article_update_link(topic):
    client = zulip.Client(email=ZULIP_EMAIL, client="test-github-client/0.1")
    request: Dict[str, Any] = {
        "anchor": "newest",
        "num_before": 1,
        "num_after": 0,
        "narrow": [
            {"operator": "sender", "operand": ZULIP_EMAIL},
            {"operator": "stream", "operand": ZULIP_STREAM_NAME},
            {"operator": "topic", "operand": topic},
        ],
        "apply_markdown": False,
    }
    response = client.get_messages(request)
    if response["result"] == "success":
        messages = response["messages"]
        if messages:
            latest_message = messages[0]
            latest_message_content = latest_message["content"]
            url_pattern = r"\[.*?\]\((.*?)\)"
            latest_arxiv_link = re.findall(url_pattern, latest_message_content)[0]
            return latest_arxiv_link
        else:
            return None
    else:
        print(f"Failed to retrieve message or No previous messages")
        return None


# Function to fetch latest articles from arXiv


def update_zulip_stream():
    for feed_name, feed_url in RSS_FEEDS.items():
        feed = feedparser.parse(feed_url)
        topic = feed.feed.title
        last_updated_article_link = last_article_update_link(topic)
        # To avoid the case when not having an article ends up not getting to the execution part of the for loop
        flag = True if last_updated_article_link else False
        # This is to get the latest 5 articles in ascending order by time
        for article in feed.entries[:5][::-1]:
            print(feed_name)
            link = article.link
            if flag:
                if link == last_updated_article_link:
                    flag = False
                continue
            title = markdownify.markdownify(
                article.title.replace("$^{\\ast}$", "* ")
                .replace("$^*$", "* ")
                .replace("$^*$", "* ")
                .replace("$", "$$")
                .replace("\n", " ")
            )
            published = time.strftime("%d %B %Y", article.published_parsed)
            # Some rss feeds lack these fields
            author = article.author + ", " if "author" in article.keys() else ""
            summary = markdownify.markdownify(article.description)
            tags = (
                ", ".join([entry["term"] for entry in article.tags])
                if "tags" in article
                else ""
            )  # Some feeds lack tags
            message = f"\n**[{title}]({link})**\n*{author}{published}*\n\n{summary}\n\n*{tags}*"
            print(message)
            send_zulip_message(message, topic)


# Main function to check for new articles periodically
if __name__ == "__main__":
    update_zulip_stream()
