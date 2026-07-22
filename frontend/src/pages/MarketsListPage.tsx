import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listMarketGroups } from "../api/client";
import type { MarketGroupOut } from "../api/types";

export function MarketsListPage() {
  const [groups, setGroups] = useState<MarketGroupOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listMarketGroups()
      .then(setGroups)
      .catch(() => setError("Failed to load markets"));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!groups) return <p>Loading markets...</p>;
  if (groups.length === 0) return <p>No markets yet.</p>;

  return (
    <div>
      <h1>Markets</h1>
      {groups.map((group) => (
        <div key={group.id} className="market-group-card">
          <h2>{group.title}</h2>
          {group.description && <p className="muted">{group.description}</p>}
          <ul className="market-list">
            {group.markets.map((market) => (
              <li key={market.id}>
                <Link to={`/markets/${market.id}`}>{market.label}</Link>
                <span className={`status-badge status-${market.status}`}>{market.status}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
