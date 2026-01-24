import { useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { env } from "@/config/env";

export interface Message {
  role: "user" | "assistant";
  content: string;
  id: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();

  const sendMessage = useCallback(
    async (content: string) => {
      const userMessage: Message = {
        role: "user",
        content,
        id: Math.random().toString(36).substring(7),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        // Build conversation history (last 10 messages for context)
        const conversationHistory = messages.slice(-10).map((msg) => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp.toISOString(),
          metadata: msg.metadata,
        }));

        // Use the new conversation endpoint
        const response = await fetch(`${env.apiUrl}/chat/message`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: content,
            conversation_history: conversationHistory,
          }),
        });

        if (!response.ok) throw new Error("Failed to reach the Fiscal Guard");

        const data = await response.json();

        // Create assistant message from response
        const assistantMessage: Message = {
          role: "assistant",
          content: data.message,
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
          metadata: data.metadata,
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        const errorMessage: Message = {
          role: "assistant",
          content:
            "I'm sorry, I'm having trouble connecting to my systems right now.",
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [token, messages],
  );

  return {
    messages,
    sendMessage,
    isLoading,
  };
}
