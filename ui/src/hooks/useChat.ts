import { useState, useCallback } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { env } from "@/config/env";

export interface Message {
  role: "user" | "assistant";
  content: string;
  id: string;
  timestamp: Date;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuth();

  const parseAmount = (text: string): number => {
    const match = text.match(/\$?(\d+(?:\.\d{2})?)/);
    return match ? parseFloat(match[1]) : 0;
  };

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
        const amount = parseAmount(content);
        const itemName = content.split(" ").slice(0, 5).join(" ");

        const response = await fetch(`${env.apiUrl}/decisions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            item_name: itemName,
            amount: amount,
            category: "General",
            reason: content,
            urgency: "Normal",
          }),
        });

        if (!response.ok) throw new Error("Failed to reach the Fiscal Guard");

        const data = await response.json();

        const assistantMessage: Message = {
          role: "assistant",
          content:
            data.reasoning ||
            "I've analyzed your request. Here's my recommendation.",
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
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
    [token],
  );

  return {
    messages,
    sendMessage,
    isLoading,
  };
}
