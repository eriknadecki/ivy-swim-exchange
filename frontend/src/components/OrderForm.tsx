import { useState, type FormEvent } from "react";
import { ApiError, submitOrder } from "../api/client";
import type { Action, OrderOut, OrderType, Side } from "../api/types";

export function OrderForm({ marketId, onOrderPlaced }: { marketId: string; onOrderPlaced: (order: OrderOut) => void }) {
  const [side, setSide] = useState<Side>("yes");
  const [action, setAction] = useState<Action>("buy");
  const [orderType, setOrderType] = useState<OrderType>("limit");
  const [price, setPrice] = useState("50");
  const [quantity, setQuantity] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const order = await submitOrder({
        market_id: marketId,
        side,
        action,
        order_type: orderType,
        quantity: Number(quantity),
        price_cents: orderType === "limit" ? Number(price) : undefined,
      });
      onOrderPlaced(order);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Order failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="order-form" onSubmit={handleSubmit}>
      <h3>Place order</h3>
      <div className="order-form-row">
        <label>
          <input type="radio" name="action" checked={action === "buy"} onChange={() => setAction("buy")} /> Buy
        </label>
        <label>
          <input type="radio" name="action" checked={action === "sell"} onChange={() => setAction("sell")} /> Sell
        </label>
      </div>
      <div className="order-form-row">
        <label>
          <input type="radio" name="side" checked={side === "yes"} onChange={() => setSide("yes")} /> YES
        </label>
        <label>
          <input type="radio" name="side" checked={side === "no"} onChange={() => setSide("no")} /> NO
        </label>
      </div>
      <label>
        Order type
        <select value={orderType} onChange={(e) => setOrderType(e.target.value as OrderType)}>
          <option value="limit">Limit</option>
          <option value="market">Market</option>
        </select>
      </label>
      {orderType === "limit" && (
        <label>
          Price (cents, 1-99)
          <input type="number" min={1} max={99} value={price} onChange={(e) => setPrice(e.target.value)} required />
        </label>
      )}
      <label>
        Quantity
        <input type="number" min={1} value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={submitting}>
        {submitting ? "Placing..." : `${action === "buy" ? "Buy" : "Sell"} ${side.toUpperCase()}`}
      </button>
    </form>
  );
}
