import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getMeet, getMeetTicker, listMarketGroups } from "../api/client";
import { useLiveChannels } from "../api/ws";
import type { MarketGroupOut, MeetOut, TickerUpdateOut } from "../api/types";

export function MeetDetailPage() {
  const { meetId } = useParams<{ meetId: string }>();
  const [meet, setMeet] = useState<MeetOut | null>(null);
  const [ticker, setTicker] = useState<TickerUpdateOut[]>([]);
  const [groups, setGroups] = useState<MarketGroupOut[]>([]);

  useEffect(() => {
    if (!meetId) return;
    getMeet(meetId).then(setMeet).catch(() => {});
    getMeetTicker(meetId).then(setTicker).catch(() => {});
    listMarketGroups()
      .then((all) => setGroups(all.filter((g) => g.meet_id === meetId)))
      .catch(() => {});
  }, [meetId]);

  useLiveChannels(meetId ? [`meet:${meetId}:ticker`] : [], (event) => {
    if (event.type === "ticker_update" && event.meet_id === meetId) {
      setTicker((prev) => [
        { id: crypto.randomUUID(), meet_id: event.meet_id, meet_event_id: event.meet_event_id, author_id: "", body: event.body, created_at: event.created_at },
        ...prev,
      ]);
    }
  });

  if (!meet) return <p>Loading meet...</p>;

  return (
    <div>
      <h1>{meet.name}</h1>
      <p className="muted">
        {meet.meet_type} · {meet.status}
        {meet.venue ? ` · ${meet.venue}` : ""}
      </p>

      <h2>Markets</h2>
      {groups.length === 0 ? (
        <p className="muted">No markets linked to this meet yet.</p>
      ) : (
        groups.map((group) => (
          <div key={group.id} className="market-group-card">
            <h3>{group.title}</h3>
            <ul className="market-list">
              {group.markets.map((market) => (
                <li key={market.id}>
                  <Link to={`/markets/${market.id}`}>{market.label}</Link>
                  <span className={`status-badge status-${market.status}`}>{market.status}</span>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}

      <h2>Live ticker</h2>
      {ticker.length === 0 ? (
        <p className="muted">Nothing posted yet.</p>
      ) : (
        <ul className="ticker-feed">
          {ticker.map((t) => (
            <li key={t.id}>
              <span className="ticker-time">{new Date(t.created_at).toLocaleTimeString()}</span> {t.body}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
