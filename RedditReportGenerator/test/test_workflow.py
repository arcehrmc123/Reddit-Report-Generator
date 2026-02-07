import os
import sys
sys.path.insert(0, '.')

# Test if we can load core components without OpenAI API key first
try:
    print("Loading RedditReportGenerator module...")
    from RedditReportGenerator.common.utils import load_jsonl_file
    print("OK: Common utils loaded successfully")

    from RedditReportGenerator.tools.reddit_tools import load_posts, load_comments
    print("OK: Reddit tools loaded successfully")

    from RedditReportGenerator.tools.annotated import get_user_activity_count, get_user_karma
    print("OK: Annotated tools loaded successfully")

    posts = load_posts()
    comments = load_comments()
    print(f"OK: Loaded {len(posts)} posts and {len(comments)} comments")

    # Get top authors from previous test
    from RedditReportGenerator.tools.annotated import get_community_top_authors
    top_authors = get_community_top_authors(posts, comments, 10)
    print("Top authors:")
    for i, author in enumerate(top_authors, 1):
        print(f"{i}. {author['author']}: {author['activity_count']}")

    # Test getting user activity for a real author (excluding [deleted] and AutoModerator)
    real_authors = [a['author'] for a in top_authors if a['author'] not in ['[deleted]', 'AutoModerator']]
    if real_authors:
        test_user = real_authors[0]
        print(f"\nTesting analysis for user: {test_user}")

        activity_count = get_user_activity_count(test_user, posts, comments)
        print(f"Activity count: {activity_count}")

        karma = get_user_karma(test_user, posts, comments)
        print(f"Karma: {karma}")

        print("OK: Basic user analysis functions work successfully!")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    print("Stack trace:")
    print(traceback.format_exc())

print("\n---\nTest completed!")
