# Architecture

```mermaid
flowchart TD
    A[Messy disaster scenario] --> B[Security Auditor Agent]
    B -->|redacted safe input| C[Risk Triage Agent]
    C --> D[Evidence Retrieval Agent / RAG]
    D --> E[Resource Planner Agent]
    E --> F[Communication Agent]
    F --> G[Safety-reviewed JSON + public messages]

    H[MCP Server: FastMCP] --> C
    H --> D
    H --> E
    H --> B
```

## Workflow

1. Audit input for PII and prompt injection.
2. Detect hazard and urgency.
3. Retrieve relevant guideline snippets.
4. Estimate resource gaps and priority actions.
5. Generate privacy-preserving messages.
6. Save structured output for evaluation.
