import { ClarificationEvent } from "./CortexClarification";

/**
 * Parses a Cortex Agent SSE stream and extracts clarification events.
 *
 * The Cortex Agent API returns Server-Sent Events (SSE) with different message types.
 * When the agent needs user input, it may return a structured clarification event
 * that should be rendered as interactive radio buttons rather than plain text.
 *
 * Usage:
 *   const reader = response.body.getReader();
 *   const { textChunks, clarification } = await parseCortexSSE(reader);
 *
 * Integration with your existing chat:
 *   - Render textChunks as the agent's text response
 *   - If clarification is non-null, render <CortexClarification /> component
 *   - When user selects an option, send it as the next message in the thread
 */

export interface ParsedAgentResponse {
  textChunks: string[];
  clarification: ClarificationEvent | null;
  toolCalls: Array<{ name: string; input: Record<string, unknown> }>;
  toolResults: Array<{ name: string; output: string }>;
}

/**
 * Parse SSE stream from Cortex Agent REST API.
 * Handles both structured clarification events AND text-based clarification patterns.
 */
export async function parseCortexSSE(
  reader: ReadableStreamDefaultReader<Uint8Array>
): Promise<ParsedAgentResponse> {
  const decoder = new TextDecoder();
  const textChunks: string[] = [];
  const toolCalls: ParsedAgentResponse["toolCalls"] = [];
  const toolResults: ParsedAgentResponse["toolResults"] = [];
  let clarification: ClarificationEvent | null = null;
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data:")) continue;

      const jsonStr = line.slice(5).trim();
      if (jsonStr === "[DONE]") continue;

      try {
        const event = JSON.parse(jsonStr);

        // Handle different event types from Cortex Agent API
        if (event.type === "clarification" || event.delta?.type === "clarification") {
          // Structured clarification event (native API support)
          const data = event.clarification || event.delta?.clarification || event;
          clarification = {
            question: data.question || data.message || "",
            options: (data.options || []).map((opt: string | ClarificationOption) =>
              typeof opt === "string" ? { label: opt } : opt
            ),
            allowSkip: data.allow_skip ?? true,
          };
        } else if (event.type === "text" || event.delta?.type === "text") {
          // Regular text chunk
          const text = event.text || event.delta?.text || event.delta?.content || "";
          if (text) textChunks.push(text);
        } else if (event.delta?.type === "tool_use") {
          toolCalls.push({
            name: event.delta.name,
            input: event.delta.input || {},
          });
        } else if (event.delta?.type === "tool_result") {
          toolResults.push({
            name: event.delta.name || "",
            output: event.delta.content || "",
          });
        } else if (event.choices?.[0]?.delta?.content) {
          // OpenAI-compatible format fallback
          textChunks.push(event.choices[0].delta.content);
        }
      } catch {
        // Skip malformed JSON lines
      }
    }
  }

  // Fallback: detect clarification patterns in text if no structured event was found
  if (!clarification) {
    clarification = detectClarificationFromText(textChunks.join(""));
  }

  return { textChunks, clarification, toolCalls, toolResults };
}

/**
 * Fallback: Detect clarification patterns from plain text responses.
 * Useful when the agent asks questions via text rather than structured events.
 *
 * Detects patterns like:
 *   - "Would you like X or Y?"
 *   - Bullet lists with "—" descriptions
 *   - Numbered options
 */
interface ClarificationOption {
  label: string;
  description?: string;
}

function detectClarificationFromText(text: string): ClarificationEvent | null {
  // Pattern 1: Bullet points with bold labels and descriptions
  // e.g., "• **Profit center level** — compares by profit center"
  const bulletPattern = /[•\-\*]\s+\*{0,2}(.+?)\*{0,2}\s*[—\-–:]\s*(.+)/g;
  const bulletMatches = [...text.matchAll(bulletPattern)];

  if (bulletMatches.length >= 2) {
    // Extract the question (text before the first bullet)
    const firstBulletIdx = text.indexOf(bulletMatches[0][0]);
    const questionText = text.slice(0, firstBulletIdx).trim();
    const lastSentence = questionText.split(/[.!?]\s+/).pop()?.trim() || questionText;

    return {
      question: lastSentence.replace(/[:\s]+$/, ""),
      options: bulletMatches.map((m) => ({
        label: m[1].trim().replace(/\*+/g, ""),
        description: m[2].trim(),
      })),
      allowSkip: true,
    };
  }

  // Pattern 2: "Would you like X or Y?" style
  const orPattern = /would you (?:like|prefer)(?: this at)? the (.+?) or (.+?)\?/i;
  const orMatch = text.match(orPattern);

  if (orMatch) {
    return {
      question: orMatch[0],
      options: [
        { label: orMatch[1].trim() },
        { label: orMatch[2].trim() },
      ],
      allowSkip: true,
    };
  }

  return null;
}

/**
 * Helper: Call Cortex Agent API and get parsed response with clarification handling.
 *
 * Example usage in your chat component:
 *
 *   const response = await callCortexAgent({
 *     agentEndpoint: "https://<account>.snowflakecomputing.com/api/v2/cortex/agent:run",
 *     agentName: "MY_DB.MY_SCHEMA.MY_AGENT",
 *     message: "Compare Production Revenue for Nexus 2026 Q4 May Lock Forecast v3",
 *     threadId: currentThreadId,
 *     token: bearerToken,
 *   });
 *
 *   if (response.clarification) {
 *     // Render <CortexClarification /> component
 *     setClarification(response.clarification);
 *   } else {
 *     // Render text response
 *     appendMessage(response.textChunks.join(""));
 *   }
 */
export async function callCortexAgent(params: {
  agentEndpoint: string;
  agentName: string;
  message: string;
  threadId?: string;
  token: string;
}): Promise<ParsedAgentResponse> {
  const body: Record<string, unknown> = {
    model: params.agentName,
    messages: [{ role: "user", content: params.message }],
    stream: true,
  };

  if (params.threadId) {
    body.thread_id = params.threadId;
  }

  const response = await fetch(params.agentEndpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${params.token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(`Agent API error: ${response.status} ${response.statusText}`);
  }

  const reader = response.body!.getReader();
  return parseCortexSSE(reader);
}
