# Reddit Report Generator

A sophisticated social media analysis system for Reddit users and communities.

## Overview

Reddit Report Generator is a multi-agent LLM system designed to provide comprehensive, multi-perspective analysis of Reddit user and community history. It leverages Large Language Models (LLMs) to analyze from multiple angles including content analysis, user behavior, community impact, and network analysis.

## Features

- **Multi-Agent Analysis**: Specialized AI agents analyze from multiple perspectives simultaneously
  - **Multiple Perspectives**: Analyzes from various angles including content, behavior, community impact, and network
- **Intelligent Tool-Using**: LLM-powered agents that call specific Reddit tools to gather data
  - **Quality Validation**: Stateless checking of analysis results with credibility weights
- **Final Synthesis**: Comprehensive scoring and reporting mechanism

## Data Source

The system uses two Reddit datasets:
- `r_OpenAI_posts.jsonl`: 111,461 posts
- `r_OpenAI_comments.jsonl`: 1,491,460 comments

## Core Workflow

1. **Planning**: MetaController generates analysis plans with multiple perspectives
2. **Analysis**: DomainExpert agents break down questions and gather data
3. **Validation**: StatelessChecker evaluates logical consistency
4. **Synthesis**: StatelessScorer produces final comprehensive reports

## Technology Stack

- **Python**: Main programming language
- **Pydantic**: Data validation with BaseModel schemas
- **OpenAI API**: LLM integration for intelligent analysis
- **FastAPI/Gradio**: Web interface options

## Installation

```bash
# Clone repository
git clone https://github.com/your-username/reddit-report-generator.git

# Navigate to project
cd reddit-report-generator

# Install dependencies
poetry install

# Configure OpenAI API key
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### CLI Mode (Analyze from Config)

```bash
poetry run python -m RedditReportGenerator start --config config.json
```

Options:
- `--config`: Path to configuration file (default: `config.json`)
- `--pwd`: Working directory for output files (default: `.`)

### Analyze a Single User

```bash
poetry run python -m RedditReportGenerator analyze --user "username"
```

Options:
- `--user`: Reddit user ID to analyze (required)
- `--pwd`: Working directory for output files (default: `.`)
- `--openai-api-key`: Override OpenAI API key
- `--openai-base-url`: Override OpenAI base URL

### List Top Authors

```bash
poetry run python -m RedditReportGenerator list-authors --limit 10
```

### Start Gradio Demo

```bash
poetry run python -m RedditReportGenerator demo
```

### Start FastAPI Server

```bash
poetry run python -m RedditReportGenerator serve
```

## Output

Analysis results are saved to:
- `meta_plans/`: Analysis plans with perspectives
- `check_reports/`: Validation reports (JSON format)
- `score_reports/`: Final analysis reports (Markdown format)

## Project Structure

```
RedditReportGenerator/
├── common/
│   ├── data_types.py     # Pydantic models
│   └── utils.py          # Utility Utility functions
├── roles/
│   ├── domain_expert.py   # Domain expert analysts
│   ├── meta_controller.py   # Planning coordinator
│   ├── question_solver.py   # Question-solving agents
│   ├── stateless_checker.py # Quality validator
│   └── stateless_scorer.py  # Final synthesizer
├── tools/
│   ├── annotated.py       # Annotated tool definitions
│   ├── reddit_tools.py     # Reddit data analysis tools
│   └── workflow.py          # Main workflow orchestration
```

## License

This project is licensed under MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Contact

For questions, issues, or discussions, please open an issue on GitHub.
