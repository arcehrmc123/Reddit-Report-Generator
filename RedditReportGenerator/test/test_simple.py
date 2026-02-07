"""
简化测试脚本，只验证系统的核心功能而不调用LLM
"""

import sys
import json
sys.path.insert(0, '.')

print("=" * 60)
print("Reddit Report Generator - 简化功能测试")
print("=" * 60)

try:
    print("\n1. 测试数据加载...")
    from RedditReportGenerator.tools.reddit_tools import load_posts, load_comments

    posts = load_posts()
    comments = load_comments()
    print(f"   加载了 {len(posts)} 个帖子")
    print(f"   加载了 {len(comments)} 条评论")

    print("\n2. 测试用户活动分析...")
    from RedditReportGenerator.tools.annotated import (
        get_user_activity_count,
        get_user_karma,
        get_user_activity_keywords,
        get_user_activity_sentiment
    )

    # 选择一个活跃用户（排除[deleted]和AutoModerator）
    from RedditReportGenerator.tools.annotated import get_community_top_authors
    top_authors = get_community_top_authors(posts, comments, 5)
    real_authors = [a for a in top_authors if a['author'] not in ['[deleted]', 'AutoModeratorator']]

    if real_authors:
        test_user = real_authors[0]['author']
        print(f"   测试用户: {test_user}")

        # 活动计数
        activity = get_user_activity_count(test_user, posts, comments)
        print(f"   总活动数: {activity['total_activity']}")
        print(f"   - 帖子数: {activity['total_posts']}")
        print(f"   - 评论数: {activity['total_comments']}")

        # Karma分析
        karma = get_user_karma(test_user, posts, comments)
        print(f"   总Karma: {karma['total_karma']}")
        print(f"   - 帖子Karma: {karma['post_karma']}")
        print(f"   - 评论Karma: {karma['comment_karma']}")

        # 关键词提取
        keywords = get_user_activity_keywords(test_user, posts, comments, 5)
        print(f"   关键词: {', '.join(keywords)}")

        # 情感分析
        sentiment = get_user_activity_sentiment(test_user, posts, comments)
        print(f"   平均帖子情感: {sentiment['avg_post_sentiment']:.2f}")
        print(f"   平均评论情感: {sentiment['avg_comment_sentiment']:.2f}")
        print(f"   整体情感: {sentiment['overall_sentiment']:.2f}")

    print("\n3. 测试社区统计...")
    from RedditReportGenerator.tools.annotated import (
        get_community_overall_stats,
        get_community_top_authors,
        get_community_post_frequency
    )

    community_stats = get_community_overall_stats(posts, comments)
    print(f"   社区总帖子数: {community_stats['total_posts']}")
    print(f"   社区总评论数: {community_stats['total_comments']}")
    print(f"   活跃作者数: {community_stats['total_authors']}")
    print(f"   平均每帖评论数: {community_stats['avg_comments_per_post']:.2f}")

    post_frequency = get_community_post_frequency(posts)
    print(f"   平均每天帖子数: {post_frequency['avg_posts_per_day']:.2f}")

    print("\n4. 测试配置文件...")
    with open('config_small.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        print(f"   配置的用户: {config.get('users', [])}")

    with open('analysis_categories.json', 'r', encoding='utf-8') as f:
        categories = json.load(f)
        print(f"   分析类别数: {len(categories.get('categories', []))}")

    print("\n" + "=" * 60)
    print("测试完成！所有核心功能正常工作。")
    print("=" * 60)

except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    print("\n错误详情:")
    print(traceback.format_exc())
