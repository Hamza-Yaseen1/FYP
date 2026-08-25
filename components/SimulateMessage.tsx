"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

export default function SimulateMessage({ onSent }: { onSent: () => void }) {
  const [sender, setSender] = useState("");
  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!sender.trim() || !message.trim()) return;

    setSending(true);
    try {
      await apiFetch("/webhooks/whatsapp", {
        method: "POST",
        body: JSON.stringify({ sender: sender.trim(), message: message.trim() }),
      });
      setSender("");
      setMessage("");
      onSent();
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="sim-sender">Sender</Label>
          <Input
            id="sim-sender"
            placeholder="e.g. Ali"
            value={sender}
            onChange={(e) => setSender(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="sim-message">Message</Label>
          <Input
            id="sim-message"
            placeholder="e.g. Send me the FYP slides"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
          />
        </div>
      </div>
      <Button type="submit" disabled={sending || !sender.trim() || !message.trim()}>
        {sending ? "Sending..." : "Simulate WhatsApp Message"}
      </Button>
    </form>
  );
}
