import React, { useEffect, useState } from "react";
import { Button, TextInput } from "@primer/react";
import { apiFetch } from "../api/http";
import { useWorkspaceStore } from "../store/useWorkspaceStore";

interface Entry {
  id: number;
  topic: string;
}

/**
 * Topic submission form with a tracking table that lists all submitted topics.
 */
const DataEntryForm: React.FC = () => {
  const [topic, setTopic] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const setTopics = useWorkspaceStore((s) => s.setTopics);
  const addTopic = useWorkspaceStore((s) => s.addTopic);

  useEffect(() => {
    (async () => {
      try {
        const res = await apiFetch("/entries");
        if (res.ok) {
          const data: Entry[] = await res.json();
          setEntries(data);
          setTopics(data.map((e) => e.topic));
        }
      } catch {
        // ignore network errors
      }
    })();
  }, [setTopics]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic) return;
    try {
      const res = await apiFetch("/entries", {
        method: "POST",
        body: JSON.stringify({ topic }),
      });
      if (res.ok) {
        const entry: Entry = await res.json();
        setEntries((prev) => [...prev, entry]);
        addTopic(entry.topic);
        setTopic("");
      }
    } catch {
      // ignore network errors
    }
  };

  return (
    <div className="my-4">
      <form
        onSubmit={onSubmit}
        className="mb-4 d-flex flex-column flex-items-center"
      >
        <TextInput
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Enter topic"
          block
          sx={{ mb: 2, maxWidth: "28rem" }}
        />
        <Button type="submit">Add</Button>
      </form>
      {entries.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Topic</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td>{e.topic}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DataEntryForm;
