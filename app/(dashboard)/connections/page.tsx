"use client";

import { useState, useEffect } from "react";
import ConnectionList from "@/components/connections/ConnectionList";
import { Connection, getConnections } from "@/lib/api/connections";

export default function ConnectionsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchConnections = async () => {
    setIsLoading(true);
    try {
      const data = await getConnections();
      setConnections(data);
    } catch {
      setConnections([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchConnections();
  }, []);

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-6">Connected Accounts</h1>
      {isLoading ? (
        <p className="text-gray-500">Loading connections...</p>
      ) : (
        <ConnectionList connections={connections} onRefresh={fetchConnections} />
      )}
    </div>
  );
}
