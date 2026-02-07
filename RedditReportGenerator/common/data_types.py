from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class AnalysisPerspective(BaseModel):
    """Model for analysis perspectives"""
    name: str = Field(description="The name of the analysis perspective")
    description: str = Field(
        description="The description of the perspective, explaining the focus of the analysis",
    )
    prompt: str = Field(
        description="The prompt for the perspective, helping analysts to analyze effectively from this perspective",
    )
    tool_suggestions: list[str] = Field(
        description="The list of tools used in the perspective, providing suggestions for analysts",
    )
    tips: list[str] = Field(
        description="The tips for the perspective, guiding analysts to analyze more effectively",
    )


class MetaPlan(BaseModel):
    """Model for the meta analysis plan"""
    perspectives: list[AnalysisPerspective] = Field(
        description="The list of perspectives for the analysis"
    )


class TODOItem(BaseModel):
    """Model for TODO items in perspective plans"""
    question: str = Field(
        ..., description="The TODO item in the plan, in form of a question"
    )
    prompt: str = Field(
        ..., description="The detailed prompt for better handling the question"
    )


class PerspectivePlan(BaseModel):
    """Model for perspective analysis plans"""
    target: str = Field(..., description="The target of the plan")
    items: list[TODOItem] = Field(..., description="The TODO items in the plan")


class PerspectiveWeight(BaseModel):
    """Model for perspective credibility weights"""
    perspective: str = Field(description="The perspective name")
    credibility: float = Field(
        description="Credibility weight between 0.0 and 1.0", ge=0.0, le=1.0
    )
    credibility_reasoning: str = Field(
        description="Reasoning for the assigned credibility weight"
    )
    problems: List[str] = Field(
        description="List of contradictions or missing logical mistakes in the analysis"
    )


class CheckReport(BaseModel):
    """Model for check reports"""
    perspective_weights: List[PerspectiveWeight] = Field(
        description="List of analyses with their assigned credibility weights"
    )


class CheckEval(BaseModel):
    """Model for check report evaluations"""
    coherence: float = Field(
        description="Coherence with known knowledge and evaluation criteria, between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    strength: float = Field(
        description="Supporting evidence strength, between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )


class FinalReport(BaseModel):
    """Model for final intent reports"""
    check_evaluations: List[CheckEval] = Field(
        description="The evaluation of the analysis check reports in each domain"
    )
    final_analysis: str = Field(
        description="The most comprehensive analysis of the user/community"
    )
    key_insights: List[str] = Field(
        description="List of key insights from the analysis"
    )
    strengths: List[str] = Field(
        description="Strengths of the user/community"
    )
    weaknesses: List[str] = Field(
        description="Weaknesses or areas for improvement"
    )
    recommendations: List[str] = Field(
        description="Recommendations for engagement or improvement"
    )
    confidence_score: float = Field(
        description="Overall confidence score between 0.0 and 1.0", ge=0.0, le=1.0
    )
    summary: str = Field(description="Summary of the analysis and justification")
