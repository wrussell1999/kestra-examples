# Livestream with Andreas Kretz

Demo is split into X parts:
1. Simple flow that loads data, sums it, and sends it to Slack
2. Flow that loads data from an input, sums it and produces an output file, and uploads to a data lake.
3. Flow that uses external python files to perform tasks.


## Kestra's UI

Give a tour of the UI and how it makes managing orchestration easy.

Highlight:
- Dashboards
- Gantt View during Executions
- Outputs after Executions
- Topology View
- Built in documentation that shows you the task you're clicked on

## Kestra’s Declarative Workflow Creation

Go through live demo and demonstrate the following:
- Powerful Autocomplete
- Topology View to visualise what's going on
- Expressions to dynamically pass data into tasks
    - Show off expressions inside of Python to pass Inputs into the code
- Add files and access them in a Flow (swap a Script to Commands)
- Showcase Secret Management and passing to Environment Variables for Python code

## Business Logic Vs Orchestration Logic

Demonstrate the use of Namespace files and Git to allow us to sync files and orchestrate them with Kestra 

Extend the Python Commands example that passes secrets as environment variables. This shows that you can do this with any language, and also continue running your code locally outside of Kestra.

Showcase using a different programming language to achieve the same thing.

## Everything As Code or Low-code

Build a simple flow that has a mix of tasks - some built as code, and some in low-code.

Also modify the low code with code and vice versa.