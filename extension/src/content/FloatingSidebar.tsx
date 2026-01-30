/**
 * Floating sidebar for displaying cart analysis and chat
 */

import { useState, useRef, useEffect } from "react";
import type {
  CartAnalysisResponse,
  ItemDecisionResult,
  ChatMessage,
  ChatResponse,
} from "../shared/types";

interface FloatingSidebarProps {
  analysisResults: CartAnalysisResponse;
  onChatMessage: (
    message: string,
    history: ChatMessage[],
  ) => Promise<ChatResponse>;
  onClose: () => void;
  isLoading?: boolean;
}

export function FloatingSidebar({
  analysisResults,
  onChatMessage,
  onClose,
  isLoading = false,
}: FloatingSidebarProps) {
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isSending, setIsSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isSending) return;

    const userMessage = inputValue;
    setInputValue("");
    setIsSending(true);

    // Add user message to history
    const newUserMessage: ChatMessage = {
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    };

    setChatHistory((prev) => [...prev, newUserMessage]);

    try {
      // Pass current chat history along with the new message
      const currentHistory = [...chatHistory, newUserMessage];
      const response = await onChatMessage(userMessage, currentHistory);

      setChatHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.message,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (error) {
      setChatHistory((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="fg-sidebar">
        <div className="fg-header">
          <div className="fg-header-title">
            <span className="fg-logo-icon">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
            </span>
            <span className="fg-title">Fiscal Guard</span>
          </div>
          <button className="fg-close-btn" onClick={onClose}>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div className="fg-content">
          <div
            className="p-4"
            style={{ display: "flex", flexDirection: "column", gap: "16px" }}
          >
            <div
              className="h-40 w-full rounded-md"
              style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
            />
            <div
              className="h-32 w-full rounded-md"
              style={{ backgroundColor: "rgba(255,255,255,0.05)" }}
            />
          </div>
        </div>
      </div>
    );
  }

  const overallScore = analysisResults.aggregate.overall_score;
  const scoreLabel = getScoreLabel(overallScore);
  const scoreColorClass = getScoreColorClass(overallScore);

  return (
    <div className="fg-sidebar">
      {/* Header */}
      <div className="fg-header">
        <div className="fg-header-title">
          <span className="fg-logo-icon">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#00FFC2"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </span>
          <span className="fg-title">Fiscal Guard</span>
        </div>
        <button className="fg-close-btn" onClick={onClose}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="fg-content">
        {/* Score Card */}
        <div className={`fg-score-card ${scoreColorClass}`}>
          <div className="fg-score-display">
            <span className="fg-score-number">{overallScore}</span>
            <span className="fg-score-total">/10</span>
          </div>
          <div className="fg-score-label">{scoreLabel}</div>
        </div>

        {/* Recommendation Text */}
        <div className="fg-recommendation-text">
          {analysisResults.aggregate.overall_recommendation}
        </div>

        {/* Total Amount */}
        <div className="fg-total-display">
          Total: ${analysisResults.aggregate.total_amount.toFixed(2)}
        </div>

        {/* Item Analysis Header */}
        <div className="fg-section-header">ITEM ANALYSIS</div>

        {/* Items List */}
        <div className="fg-items-list">
          {analysisResults.items.map((item, index) => (
            <ItemCard
              key={index}
              item={item}
              onAskAbout={(question) => {
                setInputValue(question);
              }}
            />
          ))}
        </div>

        {/* Chat History */}
        {chatHistory.length > 0 && (
          <div className="fg-chat-history">
            {chatHistory.map((msg, index) => (
              <ChatMessageBubble key={index} message={msg} />
            ))}
            <div ref={chatEndRef} />
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="fg-chat-input-container">
        <div className="fg-input-wrapper">
          <input
            type="text"
            className="fg-chat-input"
            placeholder="Ask about your purchase..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
            disabled={isSending}
          />
          <button
            onClick={handleSendMessage}
            disabled={isSending || !inputValue.trim()}
            className="fg-input-arrow-btn"
          >
            {isSending ? (
              "..."
            ) : (
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function getScoreLabel(score: number) {
  if (score <= 3) return "STRONG NO";
  if (score <= 5) return "RECONSIDER";
  if (score <= 7) return "PROCEED WITH CAUTION";
  return "GOOD PURCHASE";
}

function getScoreColorClass(score: number) {
  if (score <= 3) return "bg-red";
  if (score <= 5) return "bg-orange";
  if (score <= 7) return "bg-yellow";
  return "bg-green";
}

function ItemCard({
  item,
  // @ts-ignore
  onAskAbout,
}: {
  item: ItemDecisionResult;
  onAskAbout: (question: string) => void;
}) {
  const scoreColorClass = getScoreColorClass(item.decision.score);

  return (
    <div className="fg-item-card">
      <div className="fg-item-header">
        <div className="fg-item-main">
          <div className="fg-item-name">{item.item_name}</div>
          <div className="fg-item-calc">
            ${item.price.toFixed(2)} × {item.quantity} = $
            {item.total_amount.toFixed(2)}
          </div>
        </div>
        <div className={`fg-item-badge ${scoreColorClass}`}>
          {item.decision.score}/10
        </div>
      </div>
      <div className="fg-item-reasoning">{item.decision.reasoning}</div>
    </div>
  );
}

function ChatMessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`fg-chat-message ${isUser ? "user" : "assistant"}`}>
      <div className="fg-chat-bubble">{message.content}</div>
    </div>
  );
}
