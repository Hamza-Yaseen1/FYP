/**
 * TEMPORARY COMPONENT FOR LOAD TESTING
 * This component should be removed before production deployment.
 */

"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { apiFetch, clearCache } from "@/lib/api";
import { Loader2, Zap } from "lucide-react";

interface BulkTestButtonProps {
  onComplete?: () => void;
}

interface BulkResponse {
  success: boolean;
  created: number;
  requested: number;
  message_ids: string[];
  errors: string[];
}

export default function BulkTestButton({ onComplete }: BulkTestButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedCount, setSelectedCount] = useState<number | null>(null);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const handleBulkCreate = async (count: number) => {
    setIsLoading(true);
    setLastResult(null);
    setSelectedCount(count);

    try {
      const result = await apiFetch<BulkResponse>("/test/bulk-messages", {
        method: "POST",
        body: JSON.stringify({ count }),
      });
      clearCache();

      if (result.success) {
        setLastResult(`✓ Created ${result.created}/${result.requested} messages`);
        
        // Wait a bit then refresh the dashboard
        setTimeout(() => {
          onComplete?.();
        }, 1000);
      } else {
        setLastResult("⚠ Bulk creation completed with errors");
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create bulk messages";
      setLastResult(`✗ Error: ${message}`);
      console.error("Bulk creation failed:", error);
    } finally {
      setIsLoading(false);
      setSelectedCount(null);
    }
  };

  const counts = [20, 50, 100];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Zap className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">
          Load Testing (Temporary)
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {counts.map((count) => (
          <Button
            key={count}
            variant="outline"
            size="sm"
            onClick={() => handleBulkCreate(count)}
            disabled={isLoading}
            className="min-w-[80px]"
          >
            {isLoading && selectedCount === count ? (
              <>
                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                Creating...
              </>
            ) : (
              `${count} messages`
            )}
          </Button>
        ))}
      </div>

      {lastResult && (
        <div
          className={`rounded-lg border px-3 py-2 text-sm ${
            lastResult.startsWith("✓")
              ? "border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950 dark:text-green-200"
              : lastResult.startsWith("⚠")
              ? "border-yellow-200 bg-yellow-50 text-yellow-800 dark:border-yellow-900 dark:bg-yellow-950 dark:text-yellow-200"
              : "border-red-200 bg-red-50 text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
          }`}
        >
          {lastResult}
        </div>
      )}

      <p className="text-xs text-muted-foreground">
        Creates test messages that go through the full AI pipeline. Small delays between batches prevent server overload.
      </p>
    </div>
  );
}
