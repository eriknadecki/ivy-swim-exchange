import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMeets } from "../api/client";
import type { MeetOut } from "../api/types";

export function MeetsListPage() {
  const [meets, setMeets] = useState<MeetOut[] | null>(null);

  useEffect(() => {
    listMeets().then(setMeets).catch(() => {});
  }, []);

  if (!meets) return <p>Loading meets...</p>;
  if (meets.length === 0) return <p className="muted">No meets scheduled yet.</p>;

  return (
    <div>
      <h1>Meets</h1>
      <ul className="meet-list">
        {meets.map((meet) => (
          <li key={meet.id}>
            <Link to={`/meets/${meet.id}`}>{meet.name}</Link>
            <span className={`status-badge status-${meet.status}`}>{meet.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
