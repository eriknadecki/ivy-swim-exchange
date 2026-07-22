import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ApiError, cancelOrder, getMarket, getMarketBook, listMyOrders } from "../api/client";
import { useLiveChannels } from "../api/ws";
import { OrderBookView } from "../components/OrderBookView";
import { OrderForm } from "../components/OrderForm";
import type { BookSnapshotOut, MarketOut, OrderOut } from "../api/types";

interface TradeTick {
  price_cents: number;
  quantity: number;
  executed_at: string;
}

export function MarketDetailPage() {
  const { marketId } = useParams<{ marketId: string }>();
  const [market, setMarket] = useState<MarketOut | null>(null);
  const [book, setBook] = useState<BookSnapshotOut | null>(null);
  const [myOrders, setMyOrders] = useState<OrderOut[]>([]);
  const [trades, setTrades] = useState<TradeTick[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [resolvedOutcome, setResolvedOutcome] = useState<string | null>(null);

  const refreshMyOrders = useCallback(() => {
    if (!marketId) return;
    listMyOrders(marketId).then(setMyOrders).catch(() => {});
  }, [marketId]);

  useEffect(() => {
    if (!marketId) return;
    Promise.all([getMarket(marketId), getMarketBook(marketId)])
      .then(([m, b]) => {
        setMarket(m);
        setBook(b);
        setResolvedOutcome(m.resolved_outcome);
      })
      .catch(() => setError("Failed to load market"));
    refreshMyOrders();
  }, [marketId, refreshMyOrders]);

  useLiveChannels(marketId ? [`market:${marketId}`] : [], (event) => {
    if (event.type === "book_update" && event.market_id === marketId) {
      setBook({ market_id: event.market_id, bids: event.bids, asks: event.asks });
    } else if (event.type === "trade" && event.market_id === marketId) {
      setTrades((prev) => [{ price_cents: event.price_cents, quantity: event.quantity, executed_at: event.executed_at }, ...prev].slice(0, 20));
      refreshMyOrders();
    } else if (event.type === "order_update") {
      refreshMyOrders();
    } else if (event.type === "market_resolved" && event.market_id === marketId) {
      setResolvedOutcome(event.resolved_outcome);
      refreshMyOrders();
    }
  });

  async function handleCancel(orderId: string) {
    try {
      await cancelOrder(orderId);
      refreshMyOrders();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Cancel failed");
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (!market || !book) return <p>Loading market...</p>;

  return (
    <div>
      <h1>{market.label}</h1>
      {resolvedOutcome && (
        <p className="resolved-banner">
          Resolved: <strong>{resolvedOutcome.toUpperCase()}</strong>
        </p>
      )}

      <div className="market-detail-grid">
        <OrderBookView book={book} />

        <div className="market-side-panel">
          {!resolvedOutcome && <OrderForm marketId={market.id} onOrderPlaced={refreshMyOrders} />}

          <div className="trade-feed">
            <h3>Recent trades</h3>
            {trades.length === 0 && <p className="muted">No trades yet.</p>}
            <ul>
              {trades.map((t, i) => (
                <li key={i}>
                  {t.price_cents}c x {t.quantity}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="my-orders">
        <h3>My orders</h3>
        {myOrders.length === 0 && <p className="muted">No orders on this market yet.</p>}
        <table>
          <thead>
            <tr>
              <th>Action</th>
              <th>Side</th>
              <th>Price</th>
              <th>Qty</th>
              <th>Filled</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {myOrders.map((order) => (
              <tr key={order.id}>
                <td>{order.action}</td>
                <td>{order.side}</td>
                <td>{order.limit_price_cents ?? "market"}</td>
                <td>{order.quantity}</td>
                <td>{order.filled_quantity}</td>
                <td>{order.status}</td>
                <td>
                  {(order.status === "open" || order.status === "partially_filled") && (
                    <button onClick={() => handleCancel(order.id)}>Cancel</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
