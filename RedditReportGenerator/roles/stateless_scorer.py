import os
import json
import time
from typing import List
from openai import Client
from pydantic import BaseModel, Field
from RedditReportGenerator.common.utils import get_logger, try_validate_json
from RedditReportGenerator.common.data_types import CheckEval, FinalReport
from RedditReportGenerator.roles.stateless_checker import CheckReport


class StatelessScorer:
    """
    StatelessScorer is the final evaluator responsible for determining the overall analysis of the Reddit user/community.
    It aggregates all perspective analyses, checks their quality, and produces a final comprehensive report.
    """

    def __init__(self, model: str, client: Client, user_or_community_id: str):
        self.name = "StatelessScorer"
        self.model = model
        self.client = client
        self.system_message = """
ROLE: You are the final evaluator determining the comprehensive analysis of the Reddit user/community.
""".strip()
        self.log = get_logger("StatelessScorer", user_or_community_id=user_or_community_id)

    def score(
        self,
        user_or_community_id: str,
        perspective_analyst_reports: dict,
        check_report: CheckReport,
        analysis_categories: dict,
    ) -> FinalReport:
        """Score and aggregate all perspective analyses to produce a final report"""
        human_message = """
Here are different perspective analysis reports for analyzing the same Reddit user/community:
{analysis}

And a weighted assessment of intents and credibilities from each perspective is provided:
{check_report}

Evaluate step by step as below:
1. Evaluate the logical consistency of the reasoning chain in the analysis result.
2. Identify any contradictions or missing logical links.
3. Explain the reasoning behind any detected inconsistencies.
4. Synthesize all perspectives into a comprehensive final analysis.
5. Identify key insights from the analysis.
6. Highlight strengths and weaknesses/areas for improvement.
7. Provide actionable recommendations.
8. Calculate an overall confidence score.

Wrap the output in `json` tags with the structure of the FinalReport.

{final_report_schema}
""".strip()

        system_message = self.system_message.format(
            categories=json.dumps(analysis_categories),
        )

        analysis = ""
        for perspective, report in perspective_analyst_reports.items():
            analysis += f"Report on {perspective} perspective:\n{report}\n\n"

        messages = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": human_message.format(
                    final_report_schema=FinalReport.model_json_schema(),
                    check_report=check_report,
                    analysis=analysis,
                ).strip(),
            },
        ]

        self.log.debug(messages)

        while True:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0
                )

                response = completion.choices[0].message.content
                self.log.debug(response)

                reports = [
                    try_validate_json(FinalReport, no_prefix.strip("\n```"))
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
                self.log.error(f"Error in scoring: {e}")
                time.sleep(10)
                continue

        os.makedirs("score_reports", exist_ok=True)
        with open(f"score_reports/{user_or_community_id}.output.md", "w") as f:
            f.write(self._format_report(report, perspective_analyst_reports))

        return report

    def _format_report(self, final_report: FinalReport, perspective_reports: dict) -> str:
        """Format the final report as Markdown"""
        markdown = f"""# Reddit User/Community Analysis Report

## Final Analysis
{final_report.final_analysis}

## Key Insights
{chr(10).join(f"- {insight}" for insight in final_report.key_insights)}

## Strengths
{chr(10).join(f"- {strength}" for strength in final_report.strengths)}

## Areas for Improvement
{chr(10).join(f"- {weakness}" for weakness in final_report.weaknesses)}

## Recommendations
{chr(10).join(f"- {recommendation}" for recommendation in final_report.recommendations)}

## Overall Confidence Score
{final_report.confidence_score:.2f}

## Summary
{final_report.summary}

## Perspective Reports
"""

        for perspective, report in perspective_reports.items():
            markdown += f"""
### {perspective}
{report}
"""

        return markdown
