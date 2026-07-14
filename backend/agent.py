import os
import time
from typing import Dict, List
from backend.rag_engine import RAGEngine
from backend.utils import MetricsTracker
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PodcastScriptAgent:
    """
    Agent that creates podcast scripts through planning, retrieval, criticism, and revision.
    Emphasizes grounded generation using only document content.
    """

    def __init__(self, rag_engine: RAGEngine, model: str = None):
        """
        Initialize the agent.

        Args:
            rag_engine: RAG engine for document retrieval
            model: Groq model to use (required). Check https://console.groq.com/docs/models for current available models
        """
        if not model:
            raise ValueError("Model ID is required. Check https://console.groq.com/docs/models for available models.")

        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "❌ GROQ_API_KEY is not set!\n\n"
                "Fix this:\n"
                "1. Create a .env file in the project root\n"
                "2. Add: GROQ_API_KEY=gsk-your-key-here\n"
                "3. Or set in PowerShell: $env:GROQ_API_KEY='gsk-your-key-here'\n"
                "4. Restart Streamlit: streamlit run app.py"
            )

        self.rag_engine = rag_engine
        self.model = model
        self.client = Groq(api_key=api_key)
        self.max_iterations = 3
        self.metrics_tracker = MetricsTracker()

        # System prompts for different stages
        self.planner_system = """You are an expert podcast script writer. Your task is to create a detailed outline
        for a podcast episode based on a document. The outline should have:
        1. An engaging introduction
        2. 3-5 main sections with brief descriptions
        3. A clear conclusion

        Be concise and focus on what would make an interesting 5-10 minute podcast."""

        self.expander_system = """You are a podcast script writer. Your task is to expand a given section outline
        into full script text using ONLY the provided context from the documents.

        CRITICAL RULE: You MUST use ONLY information from the provided context. If information is not in the context,
        do not include it. If you cannot find sufficient information, write: "Information not available in the provided documents."

        Make the script engaging and conversational, as if narrating to listeners."""

        self.critic_system = """You are a fact-checker for podcast scripts. Your task is to review a podcast script
        against the source document and identify any claims that are NOT supported by the document.

        Respond with:
        1. A list of unsupported claims (if any)
        2. A list of claims that are properly supported (if any)
        3. Suggestions for revision

        Be strict - if a claim isn't explicitly stated or clearly implied in the source, mark it as unsupported."""

        self.reviser_system = """You are a podcast script reviser. Based on feedback about unsupported claims,
        revise the script to:
        1. Remove or rephrase unsupported claims
        2. Ground all statements in the provided document content
        3. Maintain engaging narrative style

        Return only the revised script."""

    def plan_outline(self, document_content: str) -> str:
        """
        Plan podcast structure as outline.

        Args:
            document_content: Full document text

        Returns:
            Outline string
        """
        self.metrics_tracker.start_stage("planning")

        messages = [
            {
                "role": "system",
                "content": self.planner_system
            },
            {
                "role": "user",
                "content": f"""Based on this document, create a detailed podcast outline:

{document_content[:2000]}...

[Document continues but is truncated for brevity]

Create the outline now:"""
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=messages
        )

        outline = response.choices[0].message.content
        if not isinstance(outline, str):
            outline = str(outline)

        tokens_used = response.usage.completion_tokens

        self.metrics_tracker.end_stage("planning", tokens=tokens_used)

        return outline

    def expand_section(self, section: str, document_content: str) -> str:
        """
        Expand a single section using RAG context.

        Args:
            section: Section outline to expand
            document_content: Full document for reference

        Returns:
            Expanded script section
        """
        self.metrics_tracker.start_stage("retrieval")

        # Get relevant context from RAG
        context = self.rag_engine.get_context(section, top_k=5, max_tokens=1500)

        self.metrics_tracker.end_stage("retrieval")
        self.metrics_tracker.start_stage("expansion")

        messages = [
            {
                "role": "system",
                "content": self.expander_system
            },
            {
                "role": "user",
                "content": f"""Expand this podcast section into full script:

SECTION: {section}

AVAILABLE CONTEXT FROM DOCUMENT:
{context}

Write the expanded script section now. Remember: use ONLY the provided context."""
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=800,
            messages=messages
        )

        expanded = response.choices[0].message.content
        if not isinstance(expanded, str):
            expanded = str(expanded)

        tokens_used = response.usage.completion_tokens

        self.metrics_tracker.end_stage("expansion", tokens=tokens_used)

        return expanded

    def critique_script(self, script: str, document_content: str) -> Dict:
        """
        Critique script for factual accuracy against source.

        Args:
            script: Full podcast script to review
            document_content: Original document content

        Returns:
            Critique feedback dict
        """
        self.metrics_tracker.start_stage("criticism")

        messages = [
            {
                "role": "system",
                "content": self.critic_system
            },
            {
                "role": "user",
                "content": f"""Review this podcast script for factual accuracy against the source document:

SOURCE DOCUMENT (excerpt):
{document_content[:1500]}

PODCAST SCRIPT:
{script}

Identify claims not supported by the document:"""
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=messages
        )

        critique = response.choices[0].message.content
        if not isinstance(critique, str):
            critique = str(critique)

        tokens_used = response.usage.completion_tokens

        self.metrics_tracker.end_stage("criticism", tokens=tokens_used)

        critique_lower = critique.lower()
        has_unsupported = "unsupported" in critique_lower
        has_not_found = "not found" in critique_lower
        needs_revision = bool(has_unsupported or has_not_found)

        return {
            "feedback": critique,
            "needs_revision": needs_revision
        }

    def revise_script(self, script: str, feedback: str) -> str:
        """
        Revise script based on critic feedback.

        Args:
            script: Original script
            feedback: Critic feedback

        Returns:
            Revised script
        """
        self.metrics_tracker.start_stage("revision")

        messages = [
            {
                "role": "system",
                "content": self.reviser_system
            },
            {
                "role": "user",
                "content": f"""Revise this script based on the feedback:

ORIGINAL SCRIPT:
{script}

FEEDBACK:
{feedback}

Revise the script now:"""
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=messages
        )

        revised = response.choices[0].message.content
        if not isinstance(revised, str):
            revised = str(revised)

        tokens_used = response.usage.completion_tokens

        self.metrics_tracker.end_stage("revision", tokens=tokens_used)

        return revised

    def generate_full_script(self, document_path: str) -> str:
        """
        Generate full podcast script through plan-expand-critique-revise cycle.

        Args:
            document_path: Path to document file

        Returns:
            Final podcast script
        """
        try:
            print("Loading document...")
            from backend.utils import extract_text_from_file
            document_content = extract_text_from_file(document_path)

            print("\n[1/4] PLANNING OUTLINE...")
            outline = self.plan_outline(document_content)
            if not isinstance(outline, str):
                outline = str(outline)
            print(f"Outline created:\n{outline}\n")

            print("[2/4] EXPANDING SECTIONS...")
            sections = outline.split('\n')
            script_parts = []

            for i, section in enumerate(sections):
                section = str(section) if not isinstance(section, str) else section
                section_stripped = section.strip()
                if len(section_stripped) > 0:
                    print(f"  Expanding section {i+1}/{len(sections)}...")
                    expanded = self.expand_section(section, document_content)
                    if not isinstance(expanded, str):
                        expanded = str(expanded)
                    script_parts.append(expanded)

            full_script = "\n\n".join(script_parts)

            print("\n[3/4] CRITIQUING SCRIPT...")
            critique_result = self.critique_script(full_script, document_content)
            print(f"Critique:\n{critique_result['feedback']}\n")

            print("[4/4] REVISING IF NEEDED...")
            needs_revision = critique_result.get('needs_revision', False)
            needs_revision = bool(needs_revision)

            if needs_revision:
                print("Revisions needed, processing...")
                full_script = self.revise_script(full_script, critique_result['feedback'])
                if not isinstance(full_script, str):
                    full_script = str(full_script)
                print("Script revised!")
            else:
                print("Script approved!")

            return full_script
        except Exception as e:
            import traceback
            error_msg = f"Error in pipeline: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            raise Exception(error_msg)

    def get_metrics_report(self) -> Dict:
        """Get metrics for all pipeline stages."""
        return self.metrics_tracker.get_report()

    def print_metrics(self):
        """Print formatted metrics report."""
        self.metrics_tracker.print_report()
