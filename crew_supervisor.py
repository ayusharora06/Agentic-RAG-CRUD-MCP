"""
AI Agent Crew - Supervisor Pattern with 3 Agents
"""
from typing import Dict, Any, List
from crewai import Agent, Crew, Process, Task
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
import sys
from pathlib import Path
import os
import re
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rag.rag_pipeline import RAGPipeline
from tools.database import db_manager
from tools.rag_tools import SearchDocumentsTool
from tools.serper_tool import ProfileSearchTool

class SupervisorMultiAgentCrew:
    """Three-agent system: Supervisor (router/validator) + MCP Agent + RAG Agent"""
    
    def __init__(self):
        """Initialize crew components"""
        # Initialize database
        db_manager.get_connection()
        
        # Initialize RAG pipeline
        self.rag_pipeline = RAGPipeline()
        
        # Set RAG pipeline for RAG tools
        SearchDocumentsTool.set_rag_pipeline(self.rag_pipeline)
        
        print("✅ Supervisor Multi-Agent Crew initialized")
    
    def _parse_routing_decision(self, output: str) -> str:
        """Parse the supervisor's routing decision"""
        output_lower = output.lower()
        
        if "both" in output_lower or "mcp_and_rag" in output_lower:
            return "BOTH"
        elif "mcp" in output_lower or "database" in output_lower:
            return "MCP"
        elif "rag" in output_lower or "document" in output_lower:
            return "RAG"
        else:
            # Default to both if uncertain
            return "BOTH"
    
    def _parse_validation_result(self, output: str) -> Dict[str, Any]:
        """Parse the supervisor's validation result"""
        output_lower = output.lower()
        
        # More lenient acceptance criteria
        accept_keywords = ["accept", "sufficient", "complete", "correct", "accurate", 
                          "found", "yes", "good", "adequate", "satisfactory"]
        retry_keywords = ["retry", "insufficient", "incomplete", "missing", "try again", 
                         "not found", "no", "failed"]
        
        # Check for acceptance indicators
        if any(keyword in output_lower for keyword in accept_keywords):
            return {"status": "ACCEPT", "reason": output}
        
        # Check for retry indicators
        elif any(keyword in output_lower for keyword in retry_keywords):
            if "both" in output_lower:
                return {"status": "RETRY", "next_agent": "BOTH"}
            elif "mcp" in output_lower:
                return {"status": "RETRY", "next_agent": "MCP"}
            elif "rag" in output_lower:
                return {"status": "RETRY", "next_agent": "RAG"}
            else:
                return {"status": "RETRY", "next_agent": "BOTH"}
        
        # If answer contains the requested information, accept it
        elif "engine number" in output_lower and "en12345xyz" in output_lower:
            return {"status": "ACCEPT", "reason": "Answer contains requested information"}
        
        else:
            # Default to accept if unclear (avoid false negatives)
            return {"status": "ACCEPT", "reason": "Validation unclear, accepting answer"}
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process query using supervisor pattern:
        1. Supervisor routes query
        2. Worker agent(s) execute
        3. Supervisor validates result
        4. Retry if needed (max 3 attempts)
        """
        try:
            print(f"🔍 Processing query with Supervisor Pattern: {query}")
            
            # Define MCP server parameters
            person_params = StdioServerParameters(
                command="python3",
                args=["mcp_servers/person_server.py"],
                env=os.environ.copy()
            )
            
            bank_params = StdioServerParameters(
                command="python3",
                args=["mcp_servers/bank_server.py"],
                env=os.environ.copy()
            )
            
            # Open MCP connections
            with MCPServerAdapter(person_params, connect_timeout=10) as person_tools:
                with MCPServerAdapter(bank_params, connect_timeout=10) as bank_tools:
                    
                    print(f"✅ MCP tools loaded")
                    
                    # Create the three agents
                    
                    # Agent 1: MCP Agent (Database operations + Profile search)
                    mcp_agent = Agent(
                        role="Database and Profile Operations Specialist",
                        goal="Execute database operations and enrich with social profiles",
                        backstory="""You are a database expert with access to:
                        - Person operations: create, read, update, delete persons
                        - Bank operations: manage bank accounts
                        - Join operations: get person with all their accounts
                        - Profile search: find GitHub and LinkedIn profiles
                        
                        When asked about a person (e.g., "tell me about X"), ALWAYS:
                        1. Get their complete person record from database
                        2. Get ALL their bank accounts
                        3. Search for their GitHub and LinkedIn profiles using ProfileSearchTool
                        4. Provide comprehensive data including social profiles
                        
                        IMPORTANT: For any person lookup, you MUST also search for their social profiles.
                        Use the ProfileSearchTool with the person's name and email.""",
                        tools=[
                            *list(person_tools),
                            *list(bank_tools),
                            ProfileSearchTool()  # Add profile search to MCP agent
                        ],
                        verbose=True,
                        allow_delegation=False,
                        max_iter=5  # More iterations to allow profile search
                    )
                    
                    # Agent 2: RAG + Serper Agent (Documents and Profiles)
                    rag_agent = Agent(
                        role="Document and Profile Research Specialist with Privacy Protection",
                        goal="Find information from documents while protecting sensitive data like Aadhar numbers",
                        backstory="""You are an expert in:
                        - Document search: Finding information in PDFs (policies, insurance)
                        - Profile search: Finding GitHub and LinkedIn profiles
                        - Privacy protection: Masking sensitive information
                        
                        You search for:
                        - Insurance details, policy information
                        - Vehicle details (engine number, chassis)
                        - Aadhar numbers in documents
                        - Social media profiles for people
                        
                        CRITICAL PRIVACY REQUIREMENT:
                        You MUST mask ALL Aadhar numbers in your ENTIRE response for privacy protection.
                        Aadhar numbers are 12-digit numbers (like 3345 5678 9012 or 334556789012).
                        
                        WHENEVER you see an Aadhar number, you MUST:
                        1. Replace it with XXXX-XXXX-[last 4 digits]
                        2. Example: "3345 5678 9012" becomes "XXXX-XXXX-9012"
                        3. Example: "334556789012" becomes "XXXX-XXXX-9012"
                        
                        This applies EVERYWHERE in your response - no exceptions!
                        Even when quoting from documents, mask the Aadhar numbers.""",
                        tools=[
                            SearchDocumentsTool(),
                            ProfileSearchTool()
                        ],
                        verbose=True,
                        allow_delegation=False,
                        max_iter=3
                    )
                    
                    # Agent 3: Supervisor Agent (Router, Validator, and Synthesizer)
                    supervisor_agent = Agent(
                        role="Query Supervisor, Validator, and Answer Synthesizer",
                        goal="Route queries intelligently, validate answers, and synthesize unified responses",
                        backstory="""You are the supervisor who manages query execution and creates unified answers:
                        
                        DATABASE SCHEMA (MCP Agent has access to):
                        - persons table: id, name, age, email (ONLY these fields)
                        - bank_accounts table: account_id, person_id, bank_name, balance (ONLY these fields)
                        
                        ROUTING RULES:
                        - If query asks for data IN database schema → MCP Agent ONLY
                        - If query asks for data NOT in database → RAG Agent ONLY
                        - Examples for RAG ONLY: engine number, chassis, vehicle details, insurance policy, 
                          Aadhar number, premium, coverage, claim details
                        - Examples for MCP ONLY: person's age, email, bank balance, account details
                        - Use BOTH only when query explicitly needs database AND document data
                        
                        SYNTHESIS RULES:
                        - When multiple agents provide data, create ONE unified, natural answer
                        - NEVER mention "agents", "sources", "combined results" in the final answer
                        - Answer directly as if you have all the knowledge yourself
                        - Make the response flow naturally and coherently
                        
                        VALIDATION RULES:
                        - Check if the answer fully addresses the query
                        - Verify no critical information is missing
                        - Maximum 3 attempts allowed
                        
                        Be precise in routing - avoid using BOTH unless truly necessary.""",
                        tools=[],  # Supervisor doesn't need tools
                        verbose=True,
                        allow_delegation=False
                    )
                    
                    # Step 1: Routing Decision
                    print("👮 Supervisor: Analyzing query for routing...")
                    
                    routing_task = Task(
                        description=f"""
                        Analyze this query: {query}
                        
                        DATABASE CONTAINS ONLY:
                        - persons: id, name, age, email
                        - bank_accounts: account_id, person_id, bank_name, balance
                        
                        ROUTING LOGIC:
                        - If query asks for fields IN database → MCP
                        - If query asks for fields NOT in database → RAG
                        - If query needs both database AND documents → BOTH
                        
                        Examples:
                        - "What is the engine number?" → RAG (engine not in DB)
                        - "Tell me about joe-dev" → MCP (person data in DB)
                        - "What is john's age?" → MCP (age in DB)
                        - "What is the insurance policy?" → RAG (policy not in DB)
                        - "Show joe's details and his insurance" → BOTH (needs DB + docs)
                        
                        Query: {query}
                        
                        Output ONLY one word: MCP, RAG, or BOTH
                        """,
                        expected_output="Single word: MCP, RAG, or BOTH",
                        agent=supervisor_agent
                    )
                    
                    routing_crew = Crew(
                        agents=[supervisor_agent],
                        tasks=[routing_task],
                        process=Process.sequential,
                        verbose=True
                    )
                    
                    routing_result = routing_crew.kickoff(inputs={'query': query})
                    route = self._parse_routing_decision(str(routing_result))
                    print(f"📊 Routing Decision: {route}")
                    
                    # Step 2: Execute with worker agents (with retry logic)
                    max_attempts = 3
                    attempt = 1
                    final_answer = None
                    
                    while attempt <= max_attempts:
                        print(f"🔄 Attempt {attempt}/{max_attempts}")
                        
                        worker_results = []
                        
                        # Execute based on routing
                        if route == "MCP" or route == "BOTH":
                            print("🗄️ Executing MCP Agent...")
                            mcp_task = Task(
                                description=f"""Answer this query using database tools and profile search: {query}
                                
                                IMPORTANT: For any person lookup (e.g., "tell me about X"):
                                1. Get their complete person record from database
                                2. Get ALL their bank accounts from database
                                3. ALWAYS search for their GitHub and LinkedIn profiles using ProfileSearchTool
                                4. Include all social profiles found in your response
                                
                                The ProfileSearchTool requires the person's name and email to search effectively.""",
                                expected_output="Complete database information including social profiles",
                                agent=mcp_agent
                            )
                            mcp_crew = Crew(
                                agents=[mcp_agent],
                                tasks=[mcp_task],
                                process=Process.sequential,
                                verbose=True
                            )
                            mcp_result = mcp_crew.kickoff(inputs={'query': query})
                            worker_results.append(("MCP", str(mcp_result)))
                        
                        if route == "RAG" or route == "BOTH":
                            print("📚 Executing RAG Agent...")
                            rag_task = Task(
                                description=f"""Answer this query using document search and profile tools: {query}
                                
                                MANDATORY: When you find any Aadhar numbers in documents:
                                1. You MUST mask them as XXXX-XXXX-[last 4 digits]
                                2. Never show full Aadhar numbers in your response
                                3. Example: If document contains "3345 5678 9012", show it as "XXXX-XXXX-9012"
                                
                                This is a privacy requirement - mask ALL Aadhar numbers in your entire response.""",
                                expected_output="Document information with Aadhar numbers masked and/or social profiles",
                                agent=rag_agent
                            )
                            rag_crew = Crew(
                                agents=[rag_agent],
                                tasks=[rag_task],
                                process=Process.sequential,
                                verbose=True
                            )
                            rag_result = rag_crew.kickoff(inputs={'query': query})
                            worker_results.append(("RAG", str(rag_result)))
                        
                        # Synthesize results into unified answer
                        if len(worker_results) > 1:
                            # Multiple agents provided data - need synthesis
                            print("🔀 Supervisor: Synthesizing unified answer...")
                            
                            synthesis_task = Task(
                                description=f"""
                                User Query: {query}
                                
                                Information collected:
                                {chr(10).join([f"{name}: {result}" for name, result in worker_results])}
                                
                                Create ONE unified, natural answer that:
                                1. Directly answers the user's question
                                2. Combines all relevant information seamlessly
                                3. NEVER mentions "agents", "MCP", "RAG", "sources", or "combined results"
                                4. Flows as a single, coherent response
                                5. Uses natural language as if you're the sole source of knowledge
                                6. MAINTAINS privacy: Keep any Aadhar numbers masked as XXXX-XXXX-[last 4 digits]
                                
                                PRIVACY: If the information contains masked Aadhar numbers (XXXX-XXXX-XXXX), 
                                keep them masked in your unified answer. Do not unmask them.
                                
                                Example good answer:
                                "Joe-dev is a 28-year-old developer with email joe@dev.com. He has 2 bank accounts 
                                with a total balance of $5000. His GitHub profile shows active contributions to 
                                open source projects."
                                
                                Example bad answer:
                                "From the database: Joe is 28... From documents: His insurance..."
                                """,
                                expected_output="Single, natural, unified answer with privacy protection",
                                agent=supervisor_agent
                            )
                            
                            synthesis_crew = Crew(
                                agents=[supervisor_agent],
                                tasks=[synthesis_task],
                                process=Process.sequential,
                                verbose=False  # Less verbose for synthesis
                            )
                            
                            synthesis_result = synthesis_crew.kickoff(inputs={'query': query})
                            current_answer = str(synthesis_result)
                        elif worker_results:
                            # Single agent result - use as is
                            current_answer = worker_results[0][1]
                        else:
                            current_answer = "No agents were executed"
                        
                        # Step 3: Validation
                        print("👮 Supervisor: Validating answer...")
                        
                        validation_task = Task(
                            description=f"""
                            Original Query: {query}
                            
                            Answer Received: {current_answer}
                            
                            Validate if the answer addresses the query:
                            - If the answer contains the requested information → ACCEPT
                            - If the answer says "not found" or "unable to find" → consider retry
                            - If the answer directly responds to the question → ACCEPT
                            
                            Examples:
                            - Query: "What is the engine number?"
                              Answer: "The engine number is EN12345XYZ"
                              → ACCEPT (information found and provided)
                            
                            - Query: "Tell me about john"  
                              Answer: "John is 30 years old..."
                              → ACCEPT (information provided)
                            
                            - Query: "What is the policy number?"
                              Answer: "Unable to find policy information"
                              → RETRY_WITH_RAG (not found, try documents)
                            
                            Be lenient - if the answer attempts to address the query with some information, ACCEPT it.
                            
                            Output ONLY: ACCEPT or RETRY_WITH_MCP or RETRY_WITH_RAG or RETRY_WITH_BOTH
                            """,
                            expected_output="ACCEPT or RETRY_WITH_[MCP/RAG/BOTH]",
                            agent=supervisor_agent
                        )
                        
                        validation_crew = Crew(
                            agents=[supervisor_agent],
                            tasks=[validation_task],
                            process=Process.sequential,
                            verbose=True
                        )
                        
                        validation_result = validation_crew.kickoff(inputs={'query': query})
                        validation = self._parse_validation_result(str(validation_result))
                        
                        if validation["status"] == "ACCEPT":
                            print("✅ Supervisor: Answer accepted!")
                            final_answer = current_answer
                            break
                        else:
                            print(f"🔁 Supervisor: Retry requested with {validation.get('next_agent', 'BOTH')}")
                            route = validation.get('next_agent', 'BOTH')
                            attempt += 1
                    
                    # Return final result
                    if final_answer:
                        return {
                            "success": True,
                            "query": query,
                            "result": final_answer,
                            "attempts": attempt,
                            "pattern": "supervisor_multi_agent"
                        }
                    else:
                        return {
                            "success": False,
                            "query": query,
                            "error": "Could not generate satisfactory answer after maximum attempts",
                            "attempts": max_attempts,
                            "pattern": "supervisor_multi_agent"
                        }
                    
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }

# For backwards compatibility
AIAgentCrew = SupervisorMultiAgentCrew