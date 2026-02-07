import json
import os
from typing import Dict, List, Optional
import re
from collections import Counter

from RedditReportGenerator.common.utils import load_jsonl_file


def load_posts(file_path: str = "r_OpenAI_posts.jsonl") -> List[Dict]:
    """Load Reddit posts from JSONL file"""
    return load_jsonl_file(file_path)


def load_comments(file_path: str = "r_OpenAI_comments.jsonl") -> List[Dict]:
    """Load Reddit comments from JSONL file"""
    return load_jsonl_file(file_path)


def get_user_posts(user_id: str, posts: List[Dict]) -> List[Dict]:
    """Get all posts by a specific user (simplified version)"""
    user_posts = [post for post in posts if post.get("author") == user_id]
    # Return simplified post objects with only essential fields
    return [{
        "title": post.get("title", ""),
        "selftext": post.get("selftext", ""),
        "subreddit": post.get("subreddit", ""),
        "score": post.get("score", 0),
        "id": post.get("id", ""),
        "created": post.get("created", 0),
        "url": post.get("url", "")
    } for post in user_posts]


def get_user_comments(user_id: str, comments: List[Dict]) -> List[Dict]:
    """Get all comments by a specific user (simplified version)"""
    user_comments = [comment for comment in comments if comment.get("author") == user_id]
    # Return simplified comment objects with only essential fields
    return [{
        "body": comment.get("body", ""),
        "subreddit": comment.get("subreddit", ""),
        "score": comment.get("score", 0),
        "id": comment.get("id", ""),
        "created": comment.get("created", 0),
        "parent_id": comment.get("parent_id", "")
    } for comment in user_comments]


def get_user_activity_count(user_id: str, posts: List[Dict], comments: List[Dict]) -> Dict:
    """Get user activity count (posts and comments)"""
    user_posts = get_user_posts(user_id, posts)
    user_comments = get_user_comments(user_id, comments)

    return {
        "total_posts": len(user_posts),
        "total_comments": len(user_comments),
        "total_activity": len(user_posts) + len(user_comments)
    }


def get_user_karma(user_id: str, posts: List[Dict], comments: List[Dict]) -> Dict:
    """Get user karma from posts and comments"""
    user_posts = get_user_posts(user_id, posts)
    user_comments = get_user_comments(user_id, comments)

    post_karma = sum(post.get("score", 0) for post in user_posts)
    comment_karma = sum(comment.get("score", 0) for comment in user_comments)

    return {
        "post_karma": post_karma,
        "comment_karma": comment_karma,
        "total_karma": post_karma + comment_karma
    }


def get_top_posts(user_id: str, posts: List[Dict], limit: int = 5) -> List[Dict]:
    """Get top N posts by a user based on score (simplified version)"""
    user_posts = get_user_posts(user_id, posts)
    sorted_posts = sorted(user_posts, key=lambda x: x.get("score", 0), reverse=True)
    return [{
        "title": post.get("title", ""),
        "selftext": post.get("selftext", ""),
        "subreddit": post.get("subreddit", ""),
        "score": post.get("score", 0),
        "id": post.get("id", ""),
        "created": post.get("created", 0),
        "url": post.get("url", "")
    } for post in sorted_posts[:limit]]


def get_top_comments(user_id: str, comments: List[Dict], limit: int = 5) -> List[Dict]:
    """Get top N comments by a user based on score (simplified version)"""
    user_comments = get_user_comments(user_id, comments)
    sorted_comments = sorted(user_comments, key=lambda x: x.get("score", 0), reverse=True)
    return [{
        "body": comment.get("body", ""),
        "subreddit": comment.get("subreddit", ""),
        "score": comment.get("score", 0),
        "id": comment.get("id", ""),
        "created": comment.get("created", 0),
        "parent_id": comment.get("parent_id", "")
    } for comment in sorted_comments[:limit]]


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract keywords from text using simple frequency analysis"""
    # Remove punctuation and convert to lowercase
    text = re.sub(r"[^\w\s]", "", text.lower())
    words = text.split()

    # Remove stop words (simple list)
    stop_words = {
        "the", "and", "for", "with", "you", "that", "this", "but", "not", "are", "were",
        "was", "will", "would", "could", "should", "can", "if", "in", "on", "at", "by"
    }

    filtered_words = [word for word in words if word not in stop_words and len(word) > 3]

    # Count word frequencies
    word_counts = Counter(filtered_words)

    return [word for word, count in word_counts.most_common(top_n)]


def get_user_keywords(user_id: str, posts: List[Dict], comments: List[Dict], top_n: int = 10) -> List[str]:
    """Get top keywords from a user's posts and comments"""
    user_posts = get_user_posts(user_id, posts)
    user_comments = get_user_comments(user_id, comments)

    all_text = ""
    for post in user_posts:
        all_text += " " + (post.get("title", "") + " " + post.get("selftext", ""))

    for comment in user_comments:
        all_text += " " + comment.get("body", "")

    return extract_keywords(all_text, top_n)


def analyze_post_sentiment(text: str) -> float:
    """Analyze sentiment of text (simple implementation - placeholder for real NLP model)"""
    positive_words = ["good", "great", "excellent", "awesome", "amazing", "perfect", "wonderful", "fantastic"]
    negative_words = ["bad", "terrible", "awful", "horrible", "worst", "disappointing", "poor"]

    text = text.lower()
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)

    total_count = pos_count + neg_count
    if total_count == 0:
        return 0.0

    return (pos_count - neg_count) / total_count


def get_user_sentiment(user_id: str, posts: List[Dict], comments: List[Dict]) -> Dict:
    """Get sentiment analysis of a user's posts and comments"""
    user_posts = get_user_posts(user_id, posts)
    user_comments = get_user_comments(user_id, comments)

    post_sentiments = []
    for post in user_posts:
        text = post.get("title", "") + " " + post.get("selftext", "")
        post_sentiments.append(analyze_post_sentiment(text))

    comment_sentiments = []
    for comment in user_comments:
        text = comment.get("body", "")
        comment_sentiments.append(analyze_post_sentiment(text))

    avg_post_sentiment = sum(post_sentiments) / len(post_sentiments) if post_sentiments else 0.0
    avg_comment_sentiment = sum(comment_sentiments) / len(comment_sentiments) if comment_sentiments else 0.0
    overall_sentiment = (
        (sum(post_sentiments) + sum(comment_sentiments)) /
        (len(post_sentiments) + len(comment_sentiments))
    ) if (post_sentiments or comment_sentiments) else 0.0

    return {
        "avg_post_sentiment": avg_post_sentiment,
        "avg_comment_sentiment": avg_comment_sentiment,
        "overall_sentiment": overall_sentiment,
        "post_sentiment_count": len(post_sentiments),
        "comment_sentiment_count": len(comment_sentiments)
    }


def get_post_comment_ratio(user_id: str, posts: List[Dict], comments: List[Dict]) -> float:
    """Get ratio of posts to comments"""
    user_posts = get_user_posts(user_id, posts)
    user_comments = get_user_comments(user_id, comments)

    if len(user_comments) == 0:
        return float(len(user_posts))

    return len(user_posts) / len(user_comments)


def get_community_activity_stats(posts: List[Dict], comments: List[Dict]) -> Dict:
    """Get community activity statistics"""
    total_posts = len(posts)
    total_comments = len(comments)
    total_authors = set()

    for post in posts:
        if post.get("author"):
            total_authors.add(post["author"])

    for comment in comments:
        if comment.get("author"):
            total_authors.add(comment["author"])

    avg_comments_per_post = total_comments / total_posts if total_posts > 0 else 0.0

    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_authors": len(total_authors),
        "avg_comments_per_post": avg_comments_per_post
    }


def get_top_authors(posts: List[Dict], comments: List[Dict], limit: int = 10) -> List[Dict]:
    """Get top authors by total activity"""
    author_counts = Counter()

    for post in posts:
        if post.get("author"):
            author_counts[post["author"]] += 1

    for comment in comments:
        if comment.get("author"):
            author_counts[comment["author"]] += 1

    top_authors = []
    for author, count in author_counts.most_common(limit):
        top_authors.append({
            "author": author,
            "activity_count": count
        })

    return top_authors


def get_post_frequency_stats(posts: List[Dict]) -> Dict:
    """Get post frequency statistics"""
    if not posts:
        return {
            "total_posts": 0,
            "avg_posts_per_day": 0.0
        }

    total_posts = len(posts)

    return {
        "total_posts": total_posts,
        "avg_posts_per_day": total_posts / 30  # Assuming 30-day period for simplicity
    }
