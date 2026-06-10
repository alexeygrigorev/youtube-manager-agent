# Module 1 — Part 2 (Agents): video chop plan

Source video: `.tmp/videos/module1-agents-720p.mkv`
Transcript: `.tmp/transcripts/module1-agents.txt`
YouTube: https://www.youtube.com/watch?v=RAqLWJsLZb4
Total runtime: ~1:21:00 (live workshop, incl. course promo + Q&A)
Spec: `.tmp/module1-agents.spec`

Per the request for Part 2: the intro promo is trimmed harder, and clips are
non-contiguous where needed. Note the video covers the RAG revision *before*
the agents concept, so lesson 11's clip comes from later in the video than
lesson 12's — clips are independent, so course order still plays correctly.

## Cut points per lesson

| # | Lesson | Start | End | Notes |
|---|--------|-------|-----|-------|
| 11 | [Agents (intro)](../01-agentic-rag/lessons/11-agents-intro.md) | 13:48 | 16:55 | The conceptual "what are agents" — rigid RAG flow, the typo limitation, putting the LLM in control, agentic RAG. Starts on "So what are the agents?", ends on "...how exactly to do this." |
| 12 | [Quick RAG Revision (Optional)](../01-agentic-rag/lessons/12-rag-revision.md) | 2:37 | 13:44 | Environment note + RAG recap: ingest/rag_helper, load+index, assistant, working "How do I run Ollama locally?" test. Ends on "...it's based on FAQ" (in the 13:41–13:45 pause). Marked Optional. Upload title should include "(Optional)". |
| 13 | [Function Calling](../01-agentic-rag/lessons/13-function-calling.md) | 16:53 | 36:21 | Ask without tools → define `search` tool schema → send with tools → parse/execute → send result back → second call → answer; then token usage/cost. Internal trims below. |
| 14 | [The Agentic Loop](../01-agentic-rag/lessons/14-agentic-loop.md) | 36:21 | 1:01:04 | developer prompt, `make_call` helper, process-one-response, `while` loop, `agent_loop()`, encouraging multiple searches, stop condition, restricting off-topic questions. |
| 15 | [ToyAIKit](../01-agentic-rag/lessons/15-frameworks.md) | 1:01:04 | 1:13:34 | the framework, register tool, auto schema from docstring, runner + callback, run one prompt, cost, message history, continue conversation, interactive `run()`. |
| 16 | [Other Frameworks](../01-agentic-rag/lessons/16-other-frameworks.md) | 1:14:05 | 1:18:41 | framework-agnostic note (PydanticAI / OpenAI Agents SDK / Google ADK), module recap, "avoiding agents when you can". Ends on "...the cost is going to be more expensive." |

## Internal trims (within a lesson clip)

- **L13** — three segments concatenated:
  - keep **16:53 → 32:38** (function-calling walkthrough, ends "...for this lesson function calling is done")
  - drop **32:38 → 32:56** (sip of water + "does this course cover MLOps?")
  - keep **32:56 → 34:38** (token usage / cost question)
  - drop **34:38 → 34:54** ("someone's trying to get in my apartment")
  - keep **34:54 → 36:21** (finish the cost calculation: two calls, pay twice)

## Segments to discard (course-specific / off-content)

- **00:00 → 02:37** — welcome, "star the repo / like the video / subscribe" promo.
- **1:13:34 → 1:14:05** — Q&A: "can we access the recording?", the `.face` attribute.
- **1:18:43 → 1:21:00** — closing course logistics (start date), PydanticAI
  type-safety Q&A, sign-off.
