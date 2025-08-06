import React, { useEffect, useRef, useState } from "react";
import "./DataEntryForm.css";

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

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/entries");
        if (res.ok) {
          const data: Entry[] = await res.json();
          setEntries(data);
        }
      } catch {
        // ignore network errors
      }
    })();
  }, []);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic) return;
    try {
      const res = await fetch("/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });
      if (res.ok) {
        const entry: Entry = await res.json();
        setEntries((prev) => [...prev, entry]);
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
    <div className="data-entry">
      <form onSubmit={onSubmit} className="data-entry__form">
        <textarea
          ref={textareaRef}
          value={topic}
          onChange={handleChange}
          className="data-entry__textarea"
          placeholder="Enter topic"
          rows={1}
        />
        <button type="submit" className="data-entry__submit">
          Add
        </button>
      </form>
      {entries.length > 0 && (
        <table className="data-entry__table">
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
