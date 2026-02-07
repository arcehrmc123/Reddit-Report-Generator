import json

def test_data_loading():
    print("Testing data loading...")

    print("\nTesting posts file:")
    try:
        posts_count = 0
        with open('r_OpenAI_posts.jsonl', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 10:  # Only load first 10 lines
                    break
                line = line.strip()
                if line:
                    try:
                        post = json.loads(line)
                        posts_count += 1
                        if i < 3:  # Print first 3 posts
                            author = post.get('author', 'Unknown')
                            title = post.get('title', 'No title')
                            print(f"  Post {i+1}: Author={author}, Title={title[:50]}")
                    except Exception as e:
                        print(f"  Error parsing post line {i+1}: {e}")
        print(f"Loaded {posts_count} posts from r_OpenAI_posts.jsonl")
    except Exception as e:
        print(f"Error opening posts file: {e}")

    print("\nTesting comments file:")
    try:
        comments_count = 0
        with open('r_OpenAI_comments.jsonl', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 10:  # Only load first 10 lines
                    break
                line = line.strip()
                if line:
                    try:
                        comment = json.loads(line)
                        comments_count += 1
                        if i < 3:  # Print first 3 comments
                            author = comment.get('author', 'Unknown')
                            body = comment.get('body', 'No body')
                            print(f"  Comment {i+1}: Author={author}, Body={body[:50]}")
                    except Exception as e:
                        print(f"  Error parsing comment line {i+1}: {e}")
        print(f"Loaded {comments_count} comments from r_OpenAI_comments.jsonl")
    except Exception as e:
        print(f"Error opening comments file: {e}")

    print("\nData loading test complete!")

if __name__ == "__main__":
    test_data_loading()
