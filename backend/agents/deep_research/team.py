"""
Deep Research Team - Orchestrates multi-agent research workflow.

The team follows this workflow:
1. Research Planner creates a research plan with queries
2. Web Researcher executes searches for each query
3. Summarizer synthesizes the findings
4. Report Writer creates the final report
"""

from textwrap import dedent
from typing import Optional

from agno.agent import Agent
from agno.team import Team

from utils.models import get_llm_model
from agno.tools.reasoning import ReasoningTools
from agno.knowledge.knowledge import Knowledge
from agno.tools.knowledge import KnowledgeTools
from tools.knowledge_tool import KnowledgeTool
from agno.workflow import Workflow

from agents.deep_research.agents import (
    create_research_planner,
    create_report_writer,
    create_summarizer,
    create_web_researcher,
)
from utils import get_db_manager


def create_deep_research_team(
    user_id: Optional[str] = None,
    enable_clarification: bool = True,
) -> Team:
    """
    Create the Deep Research Team.

    This team orchestrates multiple agents to conduct comprehensive research:
    1. Plans the research structure
    2. Searches the web for information
    3. Summarizes findings
    4. Writes the final report

    Args:
        user_id: Optional user ID for memory persistence
        enable_clarification: If True, team will ask clarifying questions

    Returns:
        Configured Team instance
    """
    db = get_db_manager()

    # Create knowledge base
    knowledge = Knowledge(
        name="deep_search_kb",
        description="Deep research knowledge base",
        contents_db=db.agno_db,
        vector_db=db.get_vector_db("deep_research"),
    )

    # Create knowledge management tool
    knowledge_tool = KnowledgeTool(knowledge=knowledge)

    agno_knowledge_tools = KnowledgeTools(
        knowledge=knowledge,
        enable_think=True,
        enable_search=True,
        enable_analyze=True,
        add_few_shot=True,
    )

    # Create specialized agents
    planner = create_research_planner()
    researcher = create_web_researcher()
    summarizer = create_summarizer()
    writer = create_report_writer()

    # Create the team with the leader orchestrating the workflow
    team = Team(
        name="Deep Research Team",
        model=get_llm_model(),
        db=db.agno_db,
        members=[
            planner,
            researcher,
            summarizer,
            writer,
        ],
        tools=[
            ReasoningTools(add_instructions=True),
            knowledge_tool,
            agno_knowledge_tools,
        ],
        knowledge=knowledge,
        search_knowledge=True,
        add_history_to_context=True,
        num_history_runs=3,
        read_chat_history=True,
        enable_user_memories=True,
        enable_session_summaries=True,
        add_name_to_context=True,
        add_memories_to_context=True,
        instructions=dedent(f"""
            You are the leader of a Deep Research Team. Your job is to orchestrate
            comprehensive research on any topic.

            ## Your Team Members:
            1. **Research Planner**: Creates research plans and generates search queries
            2. **Web Researcher**: Executes web searches and gathers information
            3. **Research Summarizer**: Synthesizes and summarizes findings
            4. **Report Writer**: Writes the final comprehensive report

            ## Workflow:

            {"### Step 0: Clarification (if needed)" if enable_clarification else ""}
            {"- If the topic is vague or broad, ask the user clarifying questions" if enable_clarification else ""}
            {"- Determine: scope, audience, specific aspects to focus on" if enable_clarification else ""}
            {"- Once clarified, proceed to planning" if enable_clarification else ""}

            ### Step 1: Planning
            - Delegate to **Research Planner** to create a structured research plan
            - The plan should include 3-5 sections with 2-3 search queries each
            - Review and approve the plan before proceeding

            ### Step 2: Research
            - Delegate to **Web Researcher** to execute searches for ALL queries
            - The researcher should search for each query in the plan
            - Ensure all sections have sufficient research data

            ### Step 3: Synthesis
            - Delegate to **Research Summarizer** to synthesize all findings
            - The summarizer should identify themes, patterns, and key insights
            - Ensure important data and citations are preserved

            ### Step 4: Report Writing
            - Delegate to **Report Writer** to create the final report
            - The report should be comprehensive, well-structured, and cited
            - Include an executive summary and conclusion

            ## Guidelines:
            - Use the think tool to reason through complex decisions
            - Ensure each agent completes their task before moving to the next
            - If research is insufficient, request additional searches
            - The final report should be thorough and professionally written
            - Always include sources with URLs

            ## Output:
            The final output should be a complete research report in markdown format.
        """),
        show_members_responses=False,
        get_member_information_tool=True,
        add_member_tools_to_context=True,
        markdown=True,
        add_datetime_to_context=True,
    )

    return team


def create_deep_research_workflow(
    user_id: Optional[str] = None,
) -> Workflow:
    """
    Create a Deep Research Workflow using sequential steps.

    This is an alternative to the Team approach, using a Workflow
    for more structured execution.

    Args:
        user_id: Optional user ID for persistence

    Returns:
        Configured Workflow instance
    """
    db = get_db_manager()

    # Create agents
    planner = create_research_planner()
    researcher = create_web_researcher()
    summarizer = create_summarizer()
    writer = create_report_writer()

    # Create workflow with sequential steps
    workflow = Workflow(
        name="Deep Research Workflow",
        description="Comprehensive research from planning to final report",
        db=db.agno_db,
        steps=[planner, researcher, summarizer, writer],
    )

    return workflow


class DeepResearchTeam:
    """Wrapper class for easy usage of the Deep Research Team."""

    def __init__(
        self,
        user_id: Optional[str] = None,
        enable_clarification: bool = True,
    ):
        self._team = create_deep_research_team(user_id, enable_clarification)

    @property
    def team(self) -> Team:
        return self._team

    def run(self, topic: str, **kwargs):
        """Run research on a topic synchronously."""
        return self._team.run(topic, **kwargs)

    async def arun(self, topic: str, **kwargs):
        """Run research on a topic asynchronously."""
        return await self._team.arun(topic, **kwargs)

    def print_response(self, topic: str, stream: bool = True, **kwargs):
        """Run and print the research response."""
        return self._team.print_response(
            topic,
            stream=stream,
            stream_intermediate_steps=True,
            **kwargs,
        )

    async def aprint_response(self, topic: str, stream: bool = True, **kwargs):
        """Run and print the research response asynchronously."""
        return await self._team.aprint_response(
            topic,
            stream=stream,
            stream_intermediate_steps=True,
            **kwargs,
        )
