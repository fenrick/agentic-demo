import React, { useEffect, useRef, useState } from "react";
import { apiFetch } from "../api/http";
import { Textarea } from "@/components/ui/textarea";
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
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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
        const el = textareaRef.current;
        if (el) {
          el.style.height = "auto";
        }
      }
    } catch {
      // ignore network errors
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTopic(e.target.value);
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${el.scrollHeight}px`;
    }
  };

  return (
    <div className="my-4">
      <form
        onSubmit={onSubmit}
        className="mb-4 d-flex flex-column flex-items-center"
      >
        <Textarea
          ref={textareaRef}
          value={topic}
          onChange={handleChange}
          className="mb-2 width-full"
          style={{ resize: "none", overflow: "hidden", maxWidth: "28rem" }}
          placeholder="Enter topic"
          rows={1}
        />
        <button type="submit" className="btn">
          Add
        </button>
      </form>
      {entries.length > 0 && (
        <table className="width-full border-collapse">
          <thead>
            <tr>
              <th className="border color-bg-subtle p-2 text-left">Topic</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="border p-2">{e.topic}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DataEntryForm;
