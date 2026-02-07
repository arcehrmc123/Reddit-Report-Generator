from RedditReportGenerator.tools.reddit_tools import (
    load_posts,
    load_comments,
    get_user_posts,
    get_user_comments,
    get_user_activity_count,
    get_user_karma,
    get_top_posts,
    get_top_comments,
    extract_keywords,
    get_user_keywords,
    analyze_post_sentiment,
    get_user_sentiment,
    get_post_comment_ratio,
    get_community_activity_stats,
    get_top_authors,
    get_post_frequency_stats
)

# Global storage for posts and comments data
# This allows tool functions to access data without passing them as parameters
_global_posts = None
_global_comments = None


def set_global_data(posts=None, comments=None):
    """Set global posts and comments data for tool access"""
    global _global_posts, _global_comments
    if posts is not None:
        _global_posts = posts
    if comments is not None:
        _global_comments = comments


def get_global_data():
    """Get global posts and comments data"""
    return _global_posts, _global_comments


# Post loading and manipulation functions
def load_reddit_posts(file_path: str = "r_OpenAI_posts.jsonl"):
    """Load Reddit posts from a JSONL file



    Args:
        file_path: Path to posts JSONL file

    Returns:
        List of post dictionaries
    """
    return load_posts(file_path)


def load_reddit_comments(file_path: str = "r_OpenAI_comments.jsonl"):
    """Load Reddit comments from a JSONL file

    Args:
        file_path: Path to comments JSONL file

    Returns:
        List of comment dictionaries
    """
    return load_comments(file_path)


# User activity functions
def get_user_post_activity(user_id: str, posts: list = None):
    """Get all posts by a specific user

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)

    Returns:
        List of posts by user
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    return get_user_posts(user_id, posts)


def get_user_comment_activity(user_id: str, comments: list = None):
    """Get all comments by a specific user

    Args:
        user_id: Reddit user ID
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        List of comments by user
    """
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_user_comments(user_id, comments)


def get_user_total_activity_count(user_id: str, posts: list = None, comments: list = None):
    """Get total activity count (posts and comments) for a user

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        Dictionary with total posts, comments, and activity count
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_user_activity_count(user_id, posts, comments)


def get_user_total_karma(user_id: str, posts: list = None, comments: list = None):
    """Get total karma for a user from posts and comments

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        Dictionary with post karma, comment karma, and total karma
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_user_karma(user_id, posts, comments)


def get_user_top_posts(user_id: str, posts: list = None, limit: int = 5):
    """Get top posts by a user based on karma score

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        limit: Number of top posts to return (default: 5)

    Returns:
        List of top posts by karma
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    return get_top_posts(user_id, posts, limit)


def get_user_top_comments(user_id: str, comments: list = None, limit: int = 5):
    """Get top comments by a user based on karma score

    Args:
        user_id: Reddit user ID
        comments: List of all comments (optional, uses global if not provided)
        limit: Number of top comments to return (default: 5)

    Returns:
        List of top comments by karma
    """
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_top_comments(user_id, comments, limit)


# Content and sentiment analysis
def extract_text_keywords(text: str, top_n: int = 10):
    """Extract top keywords from text using frequency analysis

    Args:
        text: Text to analyze
        top_n: Number of top keywords to return (default: 10)

    Returns:
        List of top keywords
    """
    return extract_keywords(text, top_n)


def get_user_activity_keywords(user_id: str, posts: list = None, comments: list = None, top_n: int = 10):
    """Get top keywords from a user's posts and comments

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)
        top_n: Number of top keywords to return (default: 10)

    Returns:
        List of top keywords from user's activity
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_user_keywords(user_id, posts, comments, top_n)


def analyze_text_sentiment(text: str):
    """Analyze sentiment of text (returns value between -1 and 1)

    Args:
        text: Text to analyze

    Returns:
        Sentiment score between -1 (very negative) and 1 (very positive)
    """
    return analyze_post_sentiment(text)


def get_user_activity_sentiment(user_id: str, posts: list = None, comments: list = None):
    """Get sentiment analysis of a user's posts and comments

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        Dictionary with average post sentiment, average comment sentiment, and overall sentiment
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_user_sentiment(user_id, posts, comments)


# Activity ratio functions
def get_user_post_comment_ratio(user_id: str, posts: list = None, comments: list = None):
    """Get ratio of posts to comments for a user

    Args:
        user_id: Reddit user ID
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        Ratio of posts to comments
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_post_comment_ratio(user_id, posts, comments)


# Community analysis functions
def get_community_overall_stats(posts: list = None, comments: list = None):
    """Get overall community activity statistics

    Args:
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)

    Returns:
        Dictionary with total posts, comments, authors, and average comments per post
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_community_activity_stats(posts, comments)


def get_community_top_authors(posts: list = None, comments: list = None, limit: int = 10):
    """Get top authors in community by activity count

    Args:
        posts: List of all posts (optional, uses global if not provided)
        comments: List of all comments (optional, uses global if not provided)
        limit: Number of top authors to return (default: 10)

    Returns:
        List of top authors with activity counts
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    if comments is None:
        comments = _global_comments
    if comments is None:
        comments = load_comments()
    return get_top_authors(posts, comments, limit)


def get_community_post_frequency(posts: list = None):
    """Get post frequency statistics for community

    Args:
        posts: List of all posts (optional, uses global if not provided)

    Returns:
        Dictionary with total posts and average posts per day (30-day period)
    """
    if posts is None:
        posts = _global_posts
    if posts is None:
        posts = load_posts()
    return get_post_frequency_stats(posts)
