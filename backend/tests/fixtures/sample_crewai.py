from crewai import Agent, Task, Crew, Process

search_tool = None  # placeholder
web_tool = None  # placeholder

researcher = Agent(
    role='Researcher',
    goal='Research topics',
    tools=[search_tool, web_tool],
    allow_delegation=True
)

task = Task(description='Research AI trends', agent=researcher)
crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential)
result = crew.kickoff()
