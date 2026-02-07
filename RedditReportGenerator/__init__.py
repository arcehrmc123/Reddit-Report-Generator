"""
Reddit Report Generator - A system for analyzing Reddit user and community history using LLM-powered multi-agent analysis.

This system is inspired by the LLM4Intent architecture and adapted for social media analysis, specifically for Reddit data.
It uses a multi-agent approach with specialized roles:
- MetaController: Plans the analysis pipeline and coordinates perspectives
- DomainExpert: Analyzes from specific domain perspectives (e.g., content analysis, user behavior, community structure)
- QuestionSolver: Collects data and answers specific questions using available tools
- StatelessChecker: Validates analysis results for consistency
- StatelessScorer: Aggregates and scores all analyses to produce final report

Available tools include:
- Reddit data extraction and analysis
- Text and sentiment analysis
- Network and community analysis
- Topic modeling and keyword extraction
"""

__version__ = "1.0.0"
