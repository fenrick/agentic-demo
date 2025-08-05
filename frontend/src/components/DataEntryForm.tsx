import React, { useEffect, useState } from "react";
import "./DataEntryForm.css";

interface Entry {
  id: number;
  name: string;
  email: string;
}

/**
 * Simple data entry form with a tracking table that lists all submissions.
 */
const DataEntryForm: React.FC = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);

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
    if (!name || !email) return;
    try {
      const res = await fetch("/entries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email }),
      });
      if (res.ok) {
        const entry: Entry = await res.json();
        setEntries((prev) => [...prev, entry]);
        setName("");
        setEmail("");
      }
    } catch {
      // ignore network errors
    }
  };

  return (
    <div className="data-entry">
      <form onSubmit={onSubmit} className="data-entry__form">
        <label className="data-entry__label">
          Name
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="data-entry__input"
          />
        </label>
        <label className="data-entry__label">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="data-entry__input"
          />
        </label>
        <button type="submit" className="data-entry__submit">
          Add
        </button>
      </form>
      {entries.length > 0 && (
        <table className="data-entry__table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.id}>
                <td>{e.name}</td>
                <td>{e.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default DataEntryForm;
