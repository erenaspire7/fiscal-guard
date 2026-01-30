import { useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface StreamingMarkdownProps {
  content: string;
  className?: string;
  speed?: number; // ms per tick (not per character)
}

/**
 * Smooth "typewriter" renderer for chunked streams.
 * - Advances multiple characters per tick (fast typing)
 * - Throttles expensive markdown parsing/renders
 */
export function StreamingMarkdown({
  content,
  className,
  speed = 12,
}: StreamingMarkdownProps) {
  // The "true" character index we've revealed so far
  const indexRef = useRef(0);

  // The last index we actually committed to React state (throttled)
  const committedIndexRef = useRef(0);

  const timeoutRef = useRef<number | null>(null);
  const contentRef = useRef(content);

  // Throttling: don't update React state / markdown parse more often than this
  const COMMIT_INTERVAL_MS = 50;

  // Multi-character stepping: reveal this many chars per tick (adjusted dynamically)
  const BASE_STEP = 4;

  // Rendered state (throttled)
  const [displayedContent, setDisplayedContent] = useState("");

  // Keep latest content available to the timer closure
  useEffect(() => {
    contentRef.current = content;
  }, [content]);

  // If content resets (new message or replacement), reset animation state
  useEffect(() => {
    if (content.length < indexRef.current) {
      indexRef.current = 0;
      committedIndexRef.current = 0;
      setDisplayedContent("");
    }
  }, [content]);

  useEffect(() => {
    let lastCommitAt = 0;

    const tick = () => {
      const target = contentRef.current;
      const remaining = target.length - indexRef.current;

      if (remaining <= 0) {
        timeoutRef.current = null;

        // Ensure final state consistency
        if (committedIndexRef.current !== target.length) {
          committedIndexRef.current = target.length;
          setDisplayedContent(target);
        }
        return;
      }

      // Dynamic stepping:
      // - small remaining: normal typing
      // - large remaining (big chunk arrives): speed up so we don't lag for seconds
      const dynamicStep =
        remaining > 800
          ? 30
          : remaining > 300
            ? 18
            : remaining > 120
              ? 10
              : BASE_STEP;

      indexRef.current = Math.min(
        target.length,
        indexRef.current + dynamicStep,
      );

      const now = performance.now();
      if (
        committedIndexRef.current !== indexRef.current &&
        now - lastCommitAt >= COMMIT_INTERVAL_MS
      ) {
        committedIndexRef.current = indexRef.current;
        setDisplayedContent(target.slice(0, indexRef.current));
        lastCommitAt = now;
      }

      timeoutRef.current = setTimeout(tick, speed);
    };

    // Start the timer if needed
    if (!timeoutRef.current && indexRef.current < content.length) {
      tick();
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [content, speed]);

  const markdownComponents = useMemo(
    () => ({
      p: ({ children, ...props }: React.ComponentPropsWithoutRef<"p">) => (
        <p className="mb-3 last:mb-0" {...props}>
          {children}
        </p>
      ),
      ul: ({ children, ...props }: React.ComponentPropsWithoutRef<"ul">) => (
        <ul className="list-disc pl-4 mb-3 last:mb-0 space-y-1" {...props}>
          {children}
        </ul>
      ),
      ol: ({ children, ...props }: React.ComponentPropsWithoutRef<"ol">) => (
        <ol className="list-decimal pl-4 mb-3 last:mb-0 space-y-1" {...props}>
          {children}
        </ol>
      ),
      li: ({ children, ...props }: React.ComponentPropsWithoutRef<"li">) => (
        <li className="mb-1" {...props}>
          {children}
        </li>
      ),
      strong: ({
        children,
        ...props
      }: React.ComponentPropsWithoutRef<"strong">) => (
        <strong className="font-semibold text-primary" {...props}>
          {children}
        </strong>
      ),
    }),
    [],
  );

  return (
    <div className={cn("text-sm leading-relaxed font-sans", className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={markdownComponents}
      >
        {displayedContent}
      </ReactMarkdown>
    </div>
  );
}
