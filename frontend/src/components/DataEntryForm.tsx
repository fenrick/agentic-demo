import React, { useState } from "react";
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

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) return;
    const entry: Entry = { id: Date.now(), name, email };
    setEntries((prev) => [...prev, entry]);
    setName("");
    setEmail("");
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
