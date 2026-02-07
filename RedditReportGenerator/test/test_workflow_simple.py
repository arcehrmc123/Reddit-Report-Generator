import os
import sys
sys.path.insert(0, '.')

# Set minimal API key to prevent errors
os.environ['OPENAI_API_KEY'] = 'dummy_key_for_testing'

try:
    print("Testing simple workflow for user analysis...")

    # Load analysis categories
    import json
    with open('analysis_categories.json', 'r', encoding='utf-8') as f:
        analysis_categories = json.load(f)
    print("Analysis categories loaded successfully")

    # Load core workflow components
    from RedditReportGenerator.tools.annotated import load_reddit_posts, load_reddit_comments
    posts = load_reddit_posts()
    comments = load_reddit_comments()
    print(f"Loaded {len(posts)} posts and {len(comments)} comments")

    # Load top authors
    from RedditReportGenerator.tools.annotated import get_community_top_authors
    top_authors = get_community_top_authors(posts, comments, 5)
    real_authors = [a['author'] for a in top_authors if a['author'] not in ['[deleted]', 'AutoModerator']]

    if real_authors:
        test_user = real_authors[0]
        print(f"\nTesting workflow for user: {test_user}")

        # Import workflow function
        from RedditReportGenerator.__main__ import workflow

        # Try to run workflow - this should fail because we're using a dummy API key
        try:
            result = workflow(test_user, analysis_categories, posts, comments)
            print(f"Workflow returned result: {result}")
        except Exception as e:
            print(f"Workflow failed (expected, since we're using dummy API key): {e}")
            import traceback
            print("Stack trace:")
            print(traceback.format_exc())
    else:
        print("No real authors found in dataset")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    print("Stack trace:")
    print(traceback.format_exc())

print("\n---\nSimple workflow test completed!")
