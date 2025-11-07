#!/usr/bin/env python3
"""Quick DeepSeek API test"""

from config.llm_config import LLMConfig
from crewai import Agent, Task, Crew

config = LLMConfig()
print(f"Provider: {config.default_provider}")

llm = config.create_llm()

agent = Agent(
    role="Test Agent",
    goal="Generate one sentence",
    backstory="Testing DeepSeek API",
    llm=llm,
    verbose=False
)

task = Task(
    description="Write: 'DeepSeek is working!'",
    agent=agent,
    expected_output="One sentence"
)

crew = Crew(agents=[agent], tasks=[task], verbose=False)
result = crew.kickoff()

print(f"\n✅ DeepSeek works! Result: {result}")
print("\nDeepSeek Rate Limits:")
print("- 1M TPM (tokens per minute)")
print("- 100 RPM (requests per minute)")
print("- 10K RPD (requests per day)")
print("\nReady to generate your 10-chapter novel!")
