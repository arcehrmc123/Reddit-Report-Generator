import os
import json
import concurrent.futures
from typing import Any, Dict, List, Mapping, Optional, Tuple
from dotenv import load_dotenv
from openai import Client, OpenAI
import argparse

from RedditReportGenerator.common.utils import get_logger
from RedditReportGenerator.roles.domain_expert import DomainExpertAnalyst
from RedditReportGenerator.roles.meta_controller import MetaController
from RedditReportGenerator.roles.stateless_checker import StatelessChecker
from RedditReportGenerator.roles.question_solver import QuestionSolverAnalyst
from RedditReportGenerator.roles.stateless_scorer import StatelessScorer

from RedditReportGenerator.tools.annotated import *
from RedditReportGenerator.tools import annotated as tool_module

# Load environment variables
load_dotenv()

# Default model configuration
DEFAULT_MODEL_NAME = os.getenv("LLM_MODEL", "glm-4v")
SUMMARIZING_MODEL_NAME = os.getenv("SUMMARIZING_MODEL", DEFAULT_MODEL_NAME)
THINKING_MODEL_NAME = os.getenv("THINKING_MODEL", DEFAULT_MODEL_NAME)
TOKEN_LIMIT = 128000

# Initialize OpenAI client only when needed
client = None

# Model name can be set via command line
command_line_model = None


def collect_fact(user_or_community_id: str, posts: List[Dict], comments: List[Dict]):
    """Collect initial facts about the user or community"""
    user_posts = get_user_posts(user_or_community_id, posts)
    user_comments = get_user_comments(user_or_community_id, comments)

    # Calculate summary statistics instead of including full samples
    post_scores = [p.get("score", 0) for p in user_posts]
    comment_scores = [c.get("score", 0) for c in user_comments]

    fact = {
        "user_id": user_or_community_id,
        "total_posts": len(user_posts),
        "total_comments": len(user_comments),
        "total_activity": len(user_posts) + len(user_comments),
        "top_posts_count": min(5, len(user_posts)),
        "top_comments_count": min(5, len(user_comments)),
        "avg_post_score": sum(post_scores) / len(post_scores) if post_scores else 0,
        "avg_comment_score": sum(comment_scores) / len(comment_scores) if comment_scores else 0,
        "total_post_karma": sum(post_scores),
        "total_comment_karma": sum(comment_scores),
        # Only include minimal sample info, not full text
        "posts_count": len(user_posts),
        "comments_count": len(user_comments)
    }

    return fact


def workflow(user_or_community_id: str, analysis_categories: Mapping, posts: List[Dict], comments: List[Dict]):
    """Main workflow for analyzing a Reddit user or community"""
    logger = get_logger("Workflow", user_or_community_id)
    logger.warning(f"Analyzing user/community: {user_or_community_id}")

    # Set global data for tools to access
    tool_module.set_global_data(posts, comments)
    logger.info(f"Global data set: {len(posts)} posts, {len(comments)} comments")

    global client
    if client is None:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    all_available_tools = [
        get_user_post_activity,
        get_user_comment_activity,
        get_user_total_activity_count,
        get_user_total_karma,
        get_user_top_posts,
        get_user_top_comments,
        get_user_activity_keywords,
        get_user_activity_sentiment,
        get_user_post_comment_ratio,
        get_community_overall_stats,
        get_community_top_authors,
        get_community_post_frequency
    ]

    meta_controller = MetaController(DEFAULT_MODEL_NAME, client, user_or_community_id)
    meta_plan = meta_controller.build_meta_plan(all_available_tools)

    domain_experts = [
        DomainExpertAnalyst(
            DEFAULT_MODEL_NAME,
            client,
            user_or_community_id=user_or_community_id,
            perspective=perspective.name,
            tips=perspective.prompt
            + "\nTIPs:\n"
            + "\n- ".join(perspective.tips)
            + "\nTOOL SUGGESTIONS:\n"
            + "\n- ".join(perspective.tool_suggestions),
        )
        for perspective in meta_plan.perspectives
    ]

    transaction_fact = collect_fact(user_or_community_id, posts, comments)

    transaction_fact = collect_fact(user_or_community_id, posts, comments)

    main_analyst_reports = {}

    def run_expert(expert: DomainExpertAnalyst) -> Tuple[str, str]:
        plan = expert.breakdown(user_or_community_id)

        chat_histories = []
        for todo in plan.items:
            breakdown_question, item_prompt = todo.question, todo.prompt
            sub_analyst = QuestionSolverAnalyst(
                DEFAULT_MODEL_NAME,
                client,
                user_or_community_id=user_or_community_id,
                known_facts=transaction_fact,
                main_perspective=expert.perspective,
                tools=all_available_tools,
            )

            chat_histories = sub_analyst.analyze(
                chat_histories, breakdown_question, prompt=item_prompt
            )

        analyzed_intent = expert.analyze(analysis_categories, chat_histories)
        return expert.perspective, analyzed_intent

    # Execute analyzers sequentially to avoid API rate limiting
    for expert in domain_experts:
        perspective, analyzed_intent = run_expert(expert)
        main_analyst_reports[perspective] = analyzed_intent

    checker = StatelessChecker(DEFAULT_MODEL_NAME, client, user_or_community_id)
    check_report = checker.check(
        user_or_community_id, analysis_categories, main_analyst_reports
    )

    logger.info("check_report {}".format(check_report))

    scorer = StatelessScorer(DEFAULT_MODEL_NAME, client, user_or_community_id)
    final_report = scorer.score(
        user_or_community_id, main_analyst_reports, check_report, analysis_categories
    )

    logger.warning("Final report: {}".format(final_report))

    return {
        "perspective_reports": main_analyst_reports,
        "check_report": check_report,
        "final_report": final_report,
    }


def start():
    """Start the analysis from config file"""
    parser = argparse.ArgumentParser(description="Reddit Report Generator")
    parser.add_argument("--pwd", type=str, default=".")
    parser.add_argument("--config", type=str, default="config.json")
    parser.add_argument("--openai-api-key", type=str)
    parser.add_argument("--openai-base-url", type=str)

    args = parser.parse_args()

    config = json.load(open(args.config))

    analysis_categories = json.load(open("analysis_categories.json"))

    if args.pwd != ".":
        if not os.path.exists(args.pwd):
            os.makedirs(args.pwd)
        print(f"Creating directory: {args.pwd}")
    else:
        print(f"Using current directory: {os.getcwd()}")

    users = config.get("users", []) + config.get("communities", [])

    os.chdir(args.pwd)
    print(f"Working directory: {os.getcwd()}")

    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
    if args.openai_base_url:
        os.environ["OPENAI_API_BASE"] = args.openai_base_url

    posts = load_reddit_posts()
    comments = load_reddit_comments()

    for user_or_community_id in users:
        if os.path.exists(os.path.join("score_reports", f"{user_or_community_id}.output.md")):
            print(f"User/community {user_or_community_id} already analyzed.")
            continue
        workflow(user_or_community_id, analysis_categories, posts, comments)


def analyze_single_user():
    """Analyze a single user from command line arguments"""
    parser = argparse.ArgumentParser(description="Reddit Report Generator - Single User")
    parser.add_argument("--user", type=str, required=True, help="Reddit user ID to analyze")
    parser.add_argument("--pwd", type=str, default=".")
    parser.add_argument("--openai-api-key", type=str)
    parser.add_argument("--openai-base-url", type=str)

    args = parser.parse_args()

    analysis_categories = json.load(open("analysis_categories.json"))

    if args.pwd != ".":
        if not os.path.exists(args.pwd):
            os.makedirs(args.pwd)
        print(f"Creating directory: {args.pwd}")
    else:
        print(f"Using current directory: {os.getcwd()}")

    os.chdir(args.pwd)
    print(f"Working directory: {os.getcwd()}")

    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
    if args.openai_base_url:
        os.environ["OPENAI_API_BASE"] = args.openai_base_url

    posts = load_reddit_posts()
    comments = load_reddit_comments()

    result = workflow(args.user, analysis_categories, posts, comments)
    print(f"Analysis complete. Report saved to score_reports/{args.user}.output.md")
    return result


def list_top_authors():
    """List top authors from the dataset"""
    parser = argparse.ArgumentParser(description="List top authors from Reddit dataset")
    parser.add_argument("--limit", type=int, default=10, help="Number of top authors to list")
    # Remove the program name from sys.argv to avoid parsing errors
    import sys
    args = parser.parse_args(sys.argv[2:])

    from RedditReportGenerator.tools.annotated import load_reddit_posts, load_reddit_comments, get_community_top_authors

    posts = load_reddit_posts()
    comments = load_reddit_comments()

    top_authors = get_community_top_authors(posts, comments, args.limit)

    print(f"Top {args.limit} authors in the dataset:")
    for i, author in enumerate(top_authors, 1):
        print(f"{i}. {author['author']}: {author['activity_count']} activities")

    return top_authors


# Run with fastapi
def serve():
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    async def read_root():
        return {"Hello": "World"}

    @app.get("/start")
    async def read_item():
        return {"status": "success"}

    uvicorn.run(app, host="0.0.0.0", port=58000)


# Demo with gradio
def demo():
    import gradio as gr

    analysis_categories = json.load(open("analysis_categories.json"))

    posts = load_reddit_posts()
    comments = load_reddit_comments()

    def analyze(user_id: str):
        return workflow(user_id, analysis_categories, posts, comments)

    gr.Interface(
        fn=analyze,
        inputs="text",
        outputs="json",
        title="Reddit Report Generator",
        description="Generate comprehensive reports for Reddit users based on their activity history",
    ).launch(share=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reddit Report Generator")
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # Start command
    subparsers.add_parser("start", help="Start analysis from config file")

    # Analyze single user command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single user")
    analyze_parser.add_argument("--user", type=str, required=True, help="Reddit user ID to analyze")
    analyze_parser.add_argument("--pwd", type=str, default=".", help="Working directory")
    analyze_parser.add_argument("--openai-api-key", type=str, help="OpenAI API key")
    analyze_parser.add_argument("--openai-base-url", type=str, help="OpenAI base URL")

    # List top authors command
    list_parser = subparsers.add_parser("list-authors", help="List top authors from dataset")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of top authors to list")

    # Serve command
    subparsers.add_parser("serve", help="Start FastAPI server")

    # Demo command
    subparsers.add_parser("demo", help="Start Gradio demo")

    args = parser.parse_args()

    if args.command == "list-authors":
        list_top_authors()
    else:
        from RedditReportGenerator.roles.domain_expert import DomainExpertAnalyst
        from RedditReportGenerator.roles.meta_controller import MetaController
        from RedditReportGenerator.roles.stateless_checker import StatelessChecker
        from RedditReportGenerator.roles.question_solver import QuestionSolverAnalyst
        from RedditReportGenerator.roles.stateless_scorer import StatelessScorer

        # Initialize OpenAI client only for commands that need it
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if args.command == "start":
            start()
        elif args.command == "analyze":
            os.environ["OPENAI_API_KEY"] = args.openai_api_key or os.getenv("OPENAI_API_KEY", "")
            if args.openai_base_url:
                os.environ["OPENAI_API_BASE"] = args.openai_base_url
            os.chdir(args.pwd)
            analysis_categories = json.load(open("analysis_categories.json"))
            posts = load_reddit_posts()
            comments = load_reddit_comments()
            result = workflow(args.user, analysis_categories, posts, comments)
            print(f"Analysis complete. Report saved to score_reports/{args.user}.output.md")
        elif args.command == "serve":
            serve()
        elif args.command == "demo":
            demo()
        else:
            parser.print_help()
