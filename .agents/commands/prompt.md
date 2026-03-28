---
description: Optimize a prompt using prompt engineering best practices
---

## Task

You are an expert in prompt engineering for advanced language models and AI agents. Rewrite and improve the prompt provided in `$ARGUMENTS` to make it clearer, more structured, more efficient, and capable of producing higher quality results.

Follow this thinking process:

1. **Identify the main objective** — What is the end goal? Is it to generate code, analyze a file, refactor, answer a question?
2. **Extract key context** — What context is necessary? Does it mention specific files, technologies, or conventions?
3. **Define the task explicitly** — Reformulate the request as a direct, unambiguous instruction using clear action verbs.
4. **Structure the prompt** — Reorganize using XML tags to delimit sections. Common tags: `<context>`, `<task>`, `<instructions>`, `<example>`, `<output_format>`, `<verification_steps>`.
5. **Add verification** — How can the agent check its work is correct? (e.g. "Run the tests", "Check the linter passes", "Output must be valid JSON")
6. **Specify output format** — Define clearly how the final response should look (e.g. "Return only the code block", "Output must be a Markdown list")
7. **Include examples** — If the task benefits from it, add a concrete example inside an `<example>` tag showing the expected input/output format.

Output ONLY the optimized prompt — no explanation, no preamble, no thinking tags.
