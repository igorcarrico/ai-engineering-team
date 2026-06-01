"use client";

import { Loader2, Send, Sparkles } from "lucide-react";
import * as React from "react";

import { Markdown } from "@/components/app/markdown";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { AGENT_META, AGENT_SEQUENCE, agentMeta } from "@/lib/agents";
import { api, ApiError } from "@/lib/api";
import type { AgentKey, ChatMessage } from "@/lib/types";
import { cn, timeOfDay } from "@/lib/utils";

const SUGGESTIONS = [
  "What's the single biggest risk to validate first?",
  "What would change if we needed to ship in half the time?",
  "Walk me through how a competitor could kill this.",
  "What's the cheapest way to test the core assumption this week?",
];

export function ChatPanel({ runId, finished }: { runId: string; finished: boolean }) {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [content, setContent] = React.useState("");
  const [target, setTarget] = React.useState<AgentKey | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [historyLoaded, setHistoryLoaded] = React.useState(false);
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!finished) return;
    let cancelled = false;
    api
      .listChat(runId)
      .then((msgs) => {
        if (!cancelled) {
          setMessages(msgs);
          setHistoryLoaded(true);
        }
      })
      .catch(() => setHistoryLoaded(true));
    return () => {
      cancelled = true;
    };
  }, [runId, finished]);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, loading]);

  async function send() {
    const trimmed = content.trim();
    if (trimmed.length < 1 || loading) return;
    setLoading(true);
    setError(null);
    try {
      const exchange = await api.sendChat(runId, {
        content: trimmed,
        agent: target,
      });
      setMessages((prev) => [...prev, exchange.user, exchange.assistant]);
      setContent("");
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Couldn't reach the team. Is the backend running?",
      );
    } finally {
      setLoading(false);
    }
  }

  if (!finished) {
    return (
      <Card className="flex flex-col items-center justify-center py-16 text-center">
        <Sparkles className="mb-3 h-8 w-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          The team is still working. Once the verdict is ready, you can ask follow-up
          questions here.
        </p>
      </Card>
    );
  }

  return (
    <div className="grid gap-4">
      {/* Agent picker */}
      <Card className="p-4">
        <div className="mb-3 text-xs font-medium text-muted-foreground">Ask</div>
        <div className="flex flex-wrap gap-1.5">
          <AgentChip
            active={target === null}
            label="The team (Lead Consultant)"
            onClick={() => setTarget(null)}
          />
          {AGENT_SEQUENCE.map((key) => {
            const meta = AGENT_META[key];
            return (
              <AgentChip
                key={key}
                active={target === key}
                label={meta.label}
                color={meta.text}
                onClick={() => setTarget(key)}
              />
            );
          })}
        </div>
      </Card>

      {/* Conversation */}
      <Card className="flex flex-col">
        <div className="scrollbar-thin flex h-[440px] flex-col gap-3 overflow-y-auto p-5">
          {!historyLoaded ? (
            <div className="flex flex-1 items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-1 flex-col items-center justify-center text-center">
              <Sparkles className="mb-3 h-8 w-8 text-primary" />
              <h3 className="text-sm font-semibold">Ask the team a follow-up</h3>
              <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                Pick an agent above (or leave it on the Lead Consultant) and ask
                anything — the team will answer grounded in the verdict.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => setContent(s)}
                    className="rounded-full border border-border/70 bg-secondary/30 px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m) => <Bubble key={m.id} message={m} />)
          )}
          {loading && (
            <div className="flex items-center gap-2 px-2 pt-1 text-xs text-muted-foreground animate-fade-in-up">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              {agentMeta(target).label} is thinking…
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Composer */}
        <div className="border-t border-border/60 p-4">
          {error && (
            <p className="mb-2 text-xs text-[hsl(var(--danger))]">{error}</p>
          )}
          <div className="flex items-end gap-2">
            <Textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder={`Message ${agentMeta(target).label}…`}
              className="min-h-[60px] flex-1"
              onKeyDown={(e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === "Enter") send();
              }}
            />
            <Button onClick={send} disabled={loading || content.trim().length < 1}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Send <Send className="h-3.5 w-3.5" />
                </>
              )}
            </Button>
          </div>
          <p className="mt-1.5 text-[10px] text-muted-foreground">
            ⌘/Ctrl + Enter to send · Replies are grounded in the team's outputs, not
            applied to the plan.
          </p>
        </div>
      </Card>
    </div>
  );
}

function AgentChip({
  active,
  label,
  color,
  onClick,
}: {
  active: boolean;
  label: string;
  color?: string;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
        active
          ? "border-primary/50 bg-primary/15 text-primary"
          : "border-border/70 bg-secondary/30 text-muted-foreground hover:border-primary/30 hover:text-foreground",
      )}
    >
      <span className={cn(color && !active && color)}>{label}</span>
    </button>
  );
}

function Bubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const meta = agentMeta(message.agent);
  const Icon = meta.icon;
  return (
    <div
      className={cn(
        "flex gap-2.5 animate-fade-in-up",
        isUser ? "flex-row-reverse" : "flex-row",
      )}
    >
      <div
        className={cn(
          "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-secondary" : meta.bg,
        )}
      >
        {isUser ? (
          <span className="text-[10px] font-semibold text-muted-foreground">YOU</span>
        ) : (
          <Icon className={cn("h-3.5 w-3.5", meta.text)} />
        )}
      </div>
      <div className={cn("min-w-0 max-w-[80%]", isUser ? "items-end" : "items-start")}>
        <div className="flex items-baseline gap-2">
          <span className={cn("text-[11px] font-semibold", isUser ? "text-foreground" : meta.text)}>
            {isUser ? "You" : meta.label}
          </span>
          <span className="text-[10px] text-muted-foreground">
            {timeOfDay(message.created_at)}
          </span>
        </div>
        <div
          className={cn(
            "mt-1 rounded-2xl border px-3.5 py-2.5 text-sm",
            isUser
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border/60 bg-card",
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <Markdown content={message.content} />
          )}
        </div>
      </div>
    </div>
  );
}
