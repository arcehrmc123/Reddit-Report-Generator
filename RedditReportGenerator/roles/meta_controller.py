import os
import time
from openai import Client
from pydantic import BaseModel, Field

from RedditReportGenerator.common.utils import convert_tool, get_logger, try_validate_json
from RedditReportGenerator.common.data_types import AnalysisPerspective, MetaPlan


class MetaController:
    """
    MetaController is responsible for planning the analysis pipeline and coordinating analysis perspectives.
    It determines which domain experts to use and what perspectives to analyze based on the user/community and available tools.
    """

    def __init__(self, model: str, client: Client, user_or_community_id: str):
        self.name = "MetaController"
        self.model = model
        self.client = client
        self.user_or_community_id = user_or_community_id

        self.system_message = """
ROLE: You are the meta controller for bootstrapping the Reddit user/community analysis. You are responsible for building the analysis pipeline and coordinating the analysis perspectives.

ACTION: To analyze the Reddit user/community {user_or_community_id}, we have assembled a team with many domain expert analysts.
Based on your expertise, please devise a structured plan for each analyst to follow. The plan should include multiple perspectives, each with be auto assigned to a specific agent.
Each task should include a detailed prompt to guide the analysts effectively.

Suggest Considerations:
- Content Analysis:
    Analyze the textual content of posts and comments, including topics discussed, sentiment, language patterns, and content quality. Look for recurring themes, key interests, and communication styles.
- User Behavior:
    Analyze user activity patterns, including posting frequency, comment frequency, engagement levels (likes, comments, shares), and interaction patterns with other users.
- Community Engagement:
    Examine the user's role and impact within the community, including their influence, reputation, and contribution to discussions.
- Network Analysis:
    Analyze the user's interaction network, identifying key connections, influence patterns, and community structure within the subreddit.
- Other Perspectives:
    If you have other perspectives in mind, please add them to the plan.

Known Tools:
{tools}
""".strip()

        self.human_message = """
To analyze the Reddit user/community {user_or_community_id}, please devise a structured plan for each analyst to follow.

REQUIREMENTS for ALL analysts:
- ALL ANALYSTS SHOULD use the provided tools to gather and analyze data.
- When analyzing text content, focus on both quantitative metrics (word count, frequency) and qualitative aspects (sentiment, tone, topic relevance).
- When analyzing user behavior, consider both individual activity and comparative metrics within the community.
- For network analysis, focus on identifying key connections and influence patterns.
- Always ground your analysis in evidence from the data.

The response MUST be in the following JSON schema:

{meta_plan_schema}

Make sure your response is ONE valid JSON that follows this schema exactly
""".strip()

        self.log = get_logger("MetaController", user_or_community_id)

    def build_meta_plan(self, tools: list) -> MetaPlan:
        """Build a meta analysis plan by determining which perspectives to analyze"""
        messages = [
            {
                "role": "system",
                "content": self.system_message.format(
                    tools=[convert_tool(tool) for tool in tools],
                    user_or_community_id=self.user_or_community_id,
                ),
            },
            {
                "role": "user",
                "content": self.human_message.format(
                    user_or_community_id=self.user_or_community_id,
                    meta_plan_schema=MetaPlan.model_json_schema(),
                ),
            },
        ]

        while True:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=1,
                )
                response = completion.choices[0].message.content

                self.log.info("Meta plan response: %s", response)

                plans = [
                    try_validate_json(MetaPlan, no_prefix.strip("\n```"))
                    for no_prefix in response.split("```json\n")
                    if no_prefix and '"$defs"' not in no_prefix
                ]

                existing_plans = [plan for plan in plans if plan]

                if not existing_plans:
                    raise ValueError(
                        "No valid JSON found in the response {}".format(response)
                    )

                plan = existing_plans[0]
                break

            except Exception as e:
                self.log.error(f"Error in building meta plan: {e}")
                time.sleep(10)
                continue

        os.makedirs("meta_plans", exist_ok=True)
        with open(f"meta_plans/{self.user_or_community_id}.json", "w") as f:
            f.write(plan.model_dump_json(indent=4))

        return plan
