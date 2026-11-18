# Cortex Agent Clarification Component

React component that renders interactive multiple-choice clarification cards from Cortex Agent API responses — matching the behavior seen in Snowflake CoWork/Intelligence.

## Files

| File | Purpose |
|------|---------|
| `CortexClarification.tsx` | React component: radio buttons, Submit/Skip, custom text input |
| `CortexClarification.css` | Styles matching CoWork's card UI |
| `parseCortexSSE.ts` | SSE stream parser + fallback text-pattern detection |

## Quick Integration

```tsx
import { CortexClarification, ClarificationEvent } from "./CortexClarification";
import { callCortexAgent } from "./parseCortexSSE";
import "./CortexClarification.css";

function ChatMessage() {
  const [clarification, setClarification] = useState<ClarificationEvent | null>(null);

  async function sendMessage(text: string) {
    const response = await callCortexAgent({
      agentEndpoint: "https://<account>.snowflakecomputing.com/api/v2/cortex/agent:run",
      agentName: "MY_DB.MY_SCHEMA.MY_AGENT",
      message: text,
      threadId: currentThreadId,
      token: bearerToken,
    });

    if (response.clarification) {
      setClarification(response.clarification);
    } else {
      appendToChat(response.textChunks.join(""));
    }
  }

  return clarification ? (
    <CortexClarification
      clarification={clarification}
      onSubmit={(selected) => {
        setClarification(null);
        sendMessage(selected); // Send selection as next message in thread
      }}
      onSkip={() => setClarification(null)}
    />
  ) : null;
}
```

## How It Works

1. **Structured events**: If the Cortex Agent API returns a `clarification` event type in the SSE stream, it's parsed directly into options.

2. **Text fallback**: If the agent responds with plain text containing bullet-point options (like "• **Profit center level** — compares by..."), the parser detects the pattern and extracts structured options automatically.

3. **User selection**: When the user picks an option, send it as the next message in the same conversation thread — the agent continues from there.

## Customization

- Swap CSS for Tailwind/shadcn styling as needed
- The `ClarificationOption` interface supports `label` + optional `description`
- Set `allowSkip: false` to hide the Skip button
- The "Something else..." option with free-text input is always included
