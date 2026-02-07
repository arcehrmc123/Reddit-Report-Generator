import json
import logging
import time
from openai import Client
from pydantic import BaseModel, Field
from RedditReportGenerator.common.utils import get_logger, try_validate_json
from RedditReportGenerator.common.data_types import TODOItem, PerspectivePlan


BREAKDOWN_PROMPT = """
To analyze the Reddit user/community {user_or_community_id}, we have assembled a team with multiple analysts.

Based on known and unknown facts, please devise a short bullet-point plan for each analyst to follow. The plan should include the target of the analysis and the TODO items with detailed prompts for better handling each item.

Here are some TIPs to help you with the plan and prompts:
{tips}

Please create a plan with the following structure:
- target: A string describing what you will analyze
- items: An array of TODO items, each with:
  - question: A specific question to analyze
  - prompt: Detailed instructions for answering the question

Example format:
{{
  "target": "content themes",
  "items": [
    {{
      "question": "What are the main topics?",
      "prompt": "Analyze the keywords and themes in the posts"
    }}
  ]
}}

Please output ONLY valid JSON with this structure. Do not output the schema definition itself.
"""


class DomainExpertAnalyst:
    """
    DomainExpertAnalyst is responsible for analyzing Reddit users/communities from a specific domain perspective.
    Each expert has a specialized focus area and uses tools to gather and analyze data.
    """

    def __init__(
        self,
        model: str,
        client: Client,
        user_or_community_id: str,
        perspective: str,
        tips: str,
    ):
        self.name = "DomainExpertAnalyst"
        self.model = model
        self.client = client
        self.perspective = perspective
        self.tips = tips
        self.user_or_community_id = user_or_community_id

        self.system_message = """
ROLE: You are a professional Reddit user/community analyst on {perspective} domain. Below I will present you a request. Keep in mind that you are Ken Jennings-level with trivia, and Mensa-level with puzzles, so there should be a deep well to draw from.
ACTION: Analyze the Reddit user/community from the {perspective} perspective to uncover insights and patterns.
        """.format(
            perspective=self.perspective
        ).strip()

        self.log = get_logger(f"{perspective}-DomainExpert", user_or_community_id)
        self.plan = None

    def breakdown(self, user_or_community_id) -> PerspectivePlan:
        """Break down the analysis task into specific questions and prompts"""
        breakdown_prompt = BREAKDOWN_PROMPT.format(
            user_or_community_id=user_or_community_id,
            tips=self.tips,
            plan_json_schema=PerspectivePlan.model_json_schema(),
        )

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": breakdown_prompt},
        ]

        while True:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.7
                )
                response = completion.choices[0].message.content
                self.log.info("Breakdown response: %s", response)

                # First, try to find and parse a single PerspectivePlan object
                plan = None

                # Try parsing the entire response directly
                try:
                    # Clean up the response - remove markdown code blocks
                    cleaned_response = response.strip()
                    if cleaned_response.startswith("```json"):
                        cleaned_response = cleaned_response[7:]
                    if cleaned_response.startswith("```"):
                        cleaned_response = cleaned_response[3:]
                    if cleaned_response.endswith("```"):
                        cleaned_response = cleaned_response[:-3]
                    cleaned_response = cleaned_response.strip()

                    plan = try_validate_json(PerspectivePlan, cleaned_response)
                except Exception:
                    # Try parsing by splitting on ```json\n
                    plans = []
                    for no_prefix in response.split("```json\n"):
                        if no_prefix and '"$defs"' not in no_prefix:
                            try:
                                cleaned = no_prefix.strip("\n```").strip()
                                if cleaned:
                                    parsed_plan = try_validate_json(PerspectivePlan, cleaned)
                                    plans.append(parsed_plan)
                            except Exception:
                                pass

                    if plans:
                        plan = plans[0]

                if plan is None:
                    # Try parsing as array and take first element
                    try:
                        cleaned_response = response.strip()
                        if cleaned_response.startswith("```json"):
                            cleaned_response = cleaned_response[7:]
                        if cleaned_response.startswith("```"):
                            cleaned_response = cleaned_response[3:]
                        if cleaned_response.endswith("```"):
                            cleaned_response = cleaned_response[:-3]
                        cleaned_response = cleaned_response.strip()

                        parsed_array = json.loads(cleaned_response)
                        if isinstance(parsed_array, list) and len(parsed_array) > 0:
                            plan = PerspectivePlan(**parsed_array[0])
                    except Exception:
                        pass

                if plan is None:
                    raise ValueError(
                        "No valid JSON found in the response {}".format(response)
                    )
                break

            except Exception as e:
                self.log.error(f"Error in breakdown: {e}")
                time.sleep(10)
                continue

        self.log.info("Plan: %s", plan)
        self.plan = plan
        return plan

    def analyze(self, analysis_categories, merged_chat_history) -> str:
        """Analyze the user/community based on the gathered information and infer insights"""
        plan_text = "Here is the plan to analyze the " + self.plan.target + ":\n"
        plan_text += "\n".join(f"- {item.question}" for item in self.plan.items)

        chat_history = [
            {
                "role": "user",
                "content": "Please analyze the " + self.plan.target + ".",
            },
            {
                "role": "assistant",
                "content": plan_text,
            },
            *merged_chat_history,
        ]

        while True:
            system_message = self.system_message.format()
            messages = [
                {"role": "system", "content": system_message},
                *chat_history,
                {
                    "role": "user",
                    "content": f"""Please analyze the {self.plan.target} from the perspective of {self.perspective}.

Focus on identifying key patterns, insights, and actionable information. Your analysis should include:
- Quantifiable metrics and trends
- Qualitative observations about behavior and content
- Comparisons to community norms or averages
- Potential strengths, weaknesses, or areas for improvement

The analysis should cover categories such as:
{analysis_categories}
                    """,
                },
            ]

            self.log.debug("Analyst messages: %s", messages)

            completion = self.client.chat.completions.create(
                model=self.model, messages=messages, temperature=0
            )

            self.log.debug("Analyst completion: %s", completion)
            response = completion.choices[0].message.content

            chat_history.extend(
                [
                    {
                        "role": "user",
                        "content": "Please analyze against the retrieved data.",
                    },
                    {"role": "assistant", "content": response},
                ]
            )

            return response
