import type { BookSnapshotOut } from "../api/types";

export function OrderBookView({ book }: { book: BookSnapshotOut }) {
  return (
    <div className="order-book">
      <div className="book-side book-asks">
        <h3>Asks (sell)</h3>
        <table>
          <thead>
            <tr>
              <th>Price</th>
              <th>Qty</th>
            </tr>
          </thead>
          <tbody>
            {book.asks.length === 0 && (
              <tr>
                <td colSpan={2} className="muted">
                  —
                </td>
              </tr>
            )}
            {[...book.asks].reverse().map((lvl) => (
              <tr key={lvl.price_cents}>
                <td>{lvl.price_cents}c</td>
                <td>{lvl.total_quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="book-side book-bids">
        <h3>Bids (buy)</h3>
        <table>
          <thead>
            <tr>
              <th>Price</th>
              <th>Qty</th>
            </tr>
          </thead>
          <tbody>
            {book.bids.length === 0 && (
              <tr>
                <td colSpan={2} className="muted">
                  —
                </td>
              </tr>
            )}
            {book.bids.map((lvl) => (
              <tr key={lvl.price_cents}>
                <td>{lvl.price_cents}c</td>
                <td>{lvl.total_quantity}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
