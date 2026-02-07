import json
import os
import time
from typing import List, Dict, Any, Optional, Mapping
from openai import Client
from pydantic import BaseModel, Field

from RedditReportGenerator.common.utils import get_logger, try_validate_json
from RedditReportGenerator.common.data_types import PerspectiveWeight, CheckReport


class StatelessChecker:
    """
    StatelessChecker is responsible for checking the logical consistency and reasoning chain of analysis results.
    It evaluates the quality of the analysis from each perspective and assigns credibility weights.
    """

    def __init__(self, model: str, client: Client, user_or_community_id: str):
        self.name = "StatelessChecker"
        self.model = model
        self.client = client
        self.system_message = """
ROLE: Reddit Analysis Report Evaluator

You are an expert evaluator to check the logical consistency and reasoning chain of the analysis result. You need to evaluate the provided analysis step by step and identify any contradictions or missing logical links. You should infer the overall quality of each analysis report and assign credibility weights based on evidence quality and reasoning soundness.
""".strip()
        self.log = get_logger("StatelessChecker", user_or_community_id=user_or_community_id)

    def check(
        self,
        user_or_community_id: str,
        analysis_categories: dict,
        perspective_analyst_reports: dict,
    ) -> CheckReport:
        """Check the quality and consistency of perspective analysis reports"""
        system_message = self.system_message.format()

        analysis = ""
        for perspective, report in perspective_analyst_reports.items():
            analysis += f"Report on {perspective} perspective:\n{report}\n\n"

        analysis_content = """
Here are different perspective analysis reports for analyzing the same Reddit user/community:
{analysis}

Analyze this content, determine credibility weights for each perspective, and identify the overall quality of the analysis.
Provide justification for your credibility assessments based on:
- Evidence quality and relevance
- Reasoning soundness and logical consistency
- Completeness of analysis
- Presence of speculation vs. factual reasoning
- Consistency across perspectives
- Quality of data sources

{analysis_categories}

The response MUST be in the following JSON schema:

{check_report_schema}

Make sure your response is ONE valid JSON that follows this schema exactly.
""".format(
            analysis=analysis,
            analysis_categories=analysis_categories,
            check_report_schema=CheckReport.model_json_schema(),
        )

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": analysis_content,
            },
        ]

        self.log.debug(messages)

        while True:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0,
                )

                self.log.debug(completion)
                response = completion.choices[0].message.content

                reports = [
                    try_validate_json(CheckReport, no_prefix.strip("\n```"))
                    for no_prefix in response.split("```json\n")
                    if no_prefix and '"$defs"' not in no_prefix
                ]

                existing_reports = [report for report in reports if report]

                if not existing_reports:
                    raise ValueError(
                        "No valid JSON found in the response {}".format(response)
                    )

                report = existing_reports[0]
                break

            except Exception as e:
                self.log.error(f"Error in checking: {e}")
                time.sleep(10)
                continue

        os.makedirs("check_reports", exist_ok=True)
        with open(f"check_reports/{user_or_community_id}.json", "w") as f:
            f.write(report.model_dump_json(indent=4))

        return report
