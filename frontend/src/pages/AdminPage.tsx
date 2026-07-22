import { useState, type FormEvent } from "react";
import {
  ApiError,
  closeMarket,
  createInvite,
  createMarketGroup,
  createMeet,
  createTeam,
  postTickerUpdate,
  resolveMarketGroup,
} from "../api/client";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="admin-section">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function ResultLine({ result, error }: { result: string | null; error: string | null }) {
  if (error) return <p className="error">{error}</p>;
  if (result) return <p className="success">{result}</p>;
  return null;
}

export function AdminPage() {
  return (
    <div>
      <h1>Admin</h1>
      <InviteSection />
      <TeamSection />
      <MeetSection />
      <MarketGroupSection />
      <TickerSection />
      <CloseMarketSection />
      <ResolveSection />
    </div>
  );
}

function InviteSection() {
  const [maxUses, setMaxUses] = useState("20");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const invite = await createInvite(Number(maxUses), 90);
      setResult(`Invite code: ${invite.code} (share this with friends)`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create invite">
      <form onSubmit={handleSubmit}>
        <label>
          Max uses
          <input type="number" value={maxUses} onChange={(e) => setMaxUses(e.target.value)} min={1} />
        </label>
        <button type="submit">Create invite</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function TeamSection() {
  const [name, setName] = useState("");
  const [shortName, setShortName] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const team = await createTeam(name, shortName);
      setResult(`Created team "${team.name}" (id: ${team.id})`);
      setName("");
      setShortName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create team">
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Short name
          <input value={shortName} onChange={(e) => setShortName(e.target.value)} required />
        </label>
        <button type="submit">Create team</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function MeetSection() {
  const [name, setName] = useState("");
  const [meetType, setMeetType] = useState<"dual" | "championship">("dual");
  const [venue, setVenue] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const meet = await createMeet({ name, meet_type: meetType, venue: venue || null });
      setResult(`Created meet "${meet.name}" (id: ${meet.id})`);
      setName("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create meet">
      <form onSubmit={handleSubmit}>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Princeton vs Harvard" />
        </label>
        <label>
          Type
          <select value={meetType} onChange={(e) => setMeetType(e.target.value as "dual" | "championship")}>
            <option value="dual">Dual meet</option>
            <option value="championship">Championship</option>
          </select>
        </label>
        <label>
          Venue
          <input value={venue} onChange={(e) => setVenue(e.target.value)} />
        </label>
        <button type="submit">Create meet</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function MarketGroupSection() {
  const [title, setTitle] = useState("");
  const [outcomes, setOutcomes] = useState("Yes");
  const [meetId, setMeetId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const group = await createMarketGroup({
        title,
        outcomes: outcomes.split(",").map((s) => s.trim()).filter(Boolean),
        meet_id: meetId || null,
      });
      setResult(`Created "${group.title}" with ${group.markets.length} market(s)`);
      setTitle("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Create market group">
      <form onSubmit={handleSubmit}>
        <label>
          Title
          <input value={title} onChange={(e) => setTitle(e.target.value)} required placeholder="Who wins the meet?" />
        </label>
        <label>
          Outcomes (comma-separated; one outcome = a simple yes/no market)
          <input value={outcomes} onChange={(e) => setOutcomes(e.target.value)} required placeholder="Princeton wins" />
        </label>
        <label>
          Meet ID (optional)
          <input value={meetId} onChange={(e) => setMeetId(e.target.value)} placeholder="paste meet id" />
        </label>
        <button type="submit">Create market group</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function TickerSection() {
  const [meetId, setMeetId] = useState("");
  const [body, setBody] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await postTickerUpdate(meetId, body);
      setResult("Posted.");
      setBody("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Post ticker update">
      <form onSubmit={handleSubmit}>
        <label>
          Meet ID
          <input value={meetId} onChange={(e) => setMeetId(e.target.value)} required placeholder="paste meet id" />
        </label>
        <label>
          Update
          <input value={body} onChange={(e) => setBody(e.target.value)} required placeholder="Princeton wins the 200 Free Relay" />
        </label>
        <button type="submit">Post</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function CloseMarketSection() {
  const [marketId, setMarketId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const market = await closeMarket(marketId);
      setResult(`Market is now ${market.status}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Close market (halt trading)">
      <form onSubmit={handleSubmit}>
        <label>
          Market ID
          <input value={marketId} onChange={(e) => setMarketId(e.target.value)} required placeholder="paste market id" />
        </label>
        <button type="submit">Close market</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}

function ResolveSection() {
  const [groupId, setGroupId] = useState("");
  const [winningMarketId, setWinningMarketId] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const group = await resolveMarketGroup(groupId, winningMarketId);
      setResult(`Resolved "${group.title}" — payouts sent.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed");
    }
  }

  return (
    <Section title="Resolve market group">
      <form onSubmit={handleSubmit}>
        <label>
          Market group ID
          <input value={groupId} onChange={(e) => setGroupId(e.target.value)} required placeholder="paste group id" />
        </label>
        <label>
          Winning market ID
          <input value={winningMarketId} onChange={(e) => setWinningMarketId(e.target.value)} required placeholder="paste winning market id" />
        </label>
        <button type="submit">Resolve &amp; pay out</button>
      </form>
      <ResultLine result={result} error={error} />
    </Section>
  );
}
