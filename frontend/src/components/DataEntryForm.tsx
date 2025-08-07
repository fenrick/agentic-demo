import React, { useEffect, useRef, useState } from "react";

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
    <div className="my-4">
      <form
        onSubmit={onSubmit}
        className="mb-4 flex flex-col items-center gap-2"
      >
        <textarea
          ref={textareaRef}
          value={topic}
          onChange={handleChange}
          className="w-full max-w-md resize-none overflow-hidden rounded border border-gray-300 p-2"
          placeholder="Enter topic"
          rows={1}
        />
        <button type="submit" className="btn">
          Add
        </button>
      </form>
      {entries.length > 0 && (
        <table className="w-full border-collapse">
          <thead>
            <tr>
              <th className="border border-gray-300 bg-gray-100 p-2 text-left">
                Topic
              </th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="border border-gray-300 p-2">{e.topic}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DataEntryForm;
