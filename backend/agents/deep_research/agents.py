"""
Individual agents for the Deep Research team.

Each agent has a specialized role in the research process:
- Research Planner: Creates research plan and queries
- Web Researcher: Executes web searches
- Summarizer: Summarizes search results
- Report Writer: Writes the final report
"""

import os
from textwrap import dedent

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools

from utils.models import get_llm_model
from agno.tools.reasoning import ReasoningTools
from agno.tools.yfinance import YFinanceTools

from tools.mcp_tools import DynamicMCPTools


def create_research_planner() -> Agent:
    """
    Creates the Research Planner agent.

    This agent:
    - Clarifies the research topic if needed
    - Breaks down the topic into research sections
    - Generates search queries for each section
    """
    return Agent(
        name="Research Planner",
        role="Research planning and query generation",
        model=get_llm_model(),
        tools=[ReasoningTools(add_instructions=True)],
        instructions=dedent("""
            You are an expert research planner. Your job is to:

            1. CLARIFY the research topic:
               - If the topic is vague, identify what needs clarification
               - Determine the scope (broad overview vs deep dive)
               - Identify the target audience and purpose

            2. CREATE a research plan with 3-5 sections:
               - Each section should cover a distinct aspect of the topic
               - Sections should build on each other logically
               - Include: Introduction, Main Topics, Analysis, Conclusion

            3. GENERATE 2-3 search queries per section:
               - Queries should be specific and searchable
               - Include different angles (facts, trends, expert opinions)
               - Use quotation marks for exact phrases when needed

            Output your plan in a structured format:

            ## Research Plan: [Topic]

            ### Section 1: [Title]
            - Description: [What this section covers]
            - Queries:
              1. [Query 1]
              2. [Query 2]

            ### Section 2: [Title]
            ...

            Use the think tool to reason through complex topics before planning.
        """),
        add_datetime_to_context=True,
        markdown=True,
    )


def create_web_researcher() -> Agent:
    """
    Creates the Web Researcher agent.

    This agent:
    - Executes web searches using DuckDuckGo
    - Retrieves financial data using YFinance
    - Finds relevant sources and information
    - Extracts key facts and data
    """
    return Agent(
        name="Web Researcher",
        role="Web search, financial research and information gathering",
        model=get_llm_model(),
        tools=[
            DuckDuckGoTools(),
            YFinanceTools(),
        ],
        instructions=dedent("""
            You are an expert web and financial researcher. Your job is to:

            1. SEARCH for information using the provided queries
            2. EVALUATE sources for credibility and relevance
            3. EXTRACT key facts, statistics, and insights
            4. CITE sources with URLs

            ## Web Research
            For each search:
            - Execute the search query
            - Review the top results
            - Extract the most relevant information
            - Note the source URL for citation

            ## Financial Research Capabilities
            When the research involves finance, stocks, or market data, use YFinance tools:
            - Get current stock prices and market data
            - Retrieve company fundamentals (P/E ratio, market cap, etc.)
            - Access company information (sector, industry, employees)
            - Get analyst recommendations
            - Retrieve historical price data for trend analysis

            Output format for each query:

            ### Query: [The search query]

            **Key Findings:**
            - [Finding 1] (Source: [URL])
            - [Finding 2] (Source: [URL])

            **Notable Quotes:**
            > "[Quote]" - [Source]

            **Data/Statistics:**
            - [Statistic] (Source: [URL])

            **Financial Data (if applicable):**
            - [Stock/Market data from YFinance]

            Always include sources. If a search returns poor results,
            suggest alternative queries.
        """),
        add_datetime_to_context=True,
        markdown=True,
    )


def create_summarizer() -> Agent:
    """
    Creates the Summarizer agent.

    This agent:
    - Synthesizes research findings
    - Identifies patterns and themes
    - Compresses information while preserving key insights
    """
    return Agent(
        name="Research Summarizer",
        role="Synthesis and summarization of research",
        model=get_llm_model(),
        instructions=dedent("""
            You are an expert research summarizer. Your job is to:

            1. SYNTHESIZE findings from multiple sources
            2. IDENTIFY common themes and patterns
            3. HIGHLIGHT contradictions or debates
            4. COMPRESS information while keeping key insights

            For each section of research:

            **Summary:**
            [2-3 paragraph synthesis of the key findings]

            **Key Themes:**
            - [Theme 1]: [Explanation]
            - [Theme 2]: [Explanation]

            **Important Data Points:**
            - [Data point with source]

            **Gaps/Limitations:**
            - [What's missing or uncertain]

            **Sources Used:**
            - [List of sources with URLs]

            Be concise but comprehensive. Preserve all important
            information and citations.
        """),
        markdown=True,
    )


def create_report_writer(
    chart_url: str | None = None,
    pdf_url: str | None = None,
) -> Agent:
    """
    Creates the Report Writer agent.

    This agent:
    - Writes the final research report
    - Structures content logically
    - Generates charts for data visualization
    - Creates PDF exports
    - Ensures proper citations

    Args:
        chart_url: Chart generator MCP server URL (defaults to MCP_CHART_URL env var)
        pdf_url: PDF generator MCP server URL (defaults to MCP_PDF_URL env var)
    """
    chart_url = chart_url or os.environ.get("MCP_CHART_URL", "http://localhost:3003")
    pdf_url = pdf_url or os.environ.get("MCP_PDF_URL", "http://localhost:3001")

    return Agent(
        name="Report Writer",
        role="Final report writing, visualization and formatting",
        model=get_llm_model(),
        tools=[
            ReasoningTools(add_instructions=True),
            DynamicMCPTools(
                server_url=chart_url,
                name="chart_generator",
            ),
            DynamicMCPTools(
                server_url=pdf_url,
                name="pdf_generator",
            ),
        ],
        instructions=dedent("""
            You are an expert research report writer. Your job is to:

            1. STRUCTURE the report professionally:
               - Executive Summary
               - Introduction
               - Main Sections (from research plan)
               - Key Findings
               - Conclusion
               - Sources

            2. WRITE clear, engaging content:
               - Use clear headings and subheadings
               - Include relevant data and statistics
               - Cite sources inline [Source Name]
               - Use bullet points for lists
               - Include tables for comparative data

            3. VISUALIZE data with charts:
               - Use line charts for time series and trends
               - Use bar charts for comparisons
               - Use pie charts for distributions/proportions
               - Use scatter plots for correlations
               - Include charts inline in the report using markdown image syntax

            4. EXPORT the final report:
               - Generate a PDF version for professional delivery
               - Include all charts and visualizations in the PDF

            5. ENSURE quality:
               - Logical flow between sections
               - No redundancy
               - Balanced perspective
               - Actionable insights when appropriate

            Report Format:

            # [Research Topic]: A Comprehensive Analysis

            ## Executive Summary
            [3-4 sentence overview of key findings]

            ## Introduction
            [Context and scope of the research]

            ## [Section 1 Title]
            [Content with citations]
            [Chart if data visualization is helpful]

            ## [Section 2 Title]
            [Content with citations]

            ## Key Findings
            - [Finding 1]
            - [Finding 2]

            ## Conclusion
            [Summary and implications]

            ## Sources
            - [Source 1 with URL]
            - [Source 2 with URL]

            Use the think tool to plan the report structure before writing.
            Generate charts for any numerical or comparative data.
            Create a PDF export of the final report.
        """),
        add_datetime_to_context=True,
        markdown=True,
    )
