import { useEffect, useRef } from "react";
import { WS_BASE_URL, getAccessToken } from "./client";
import type { WsEvent } from "./types";

/** Opens one /ws connection, subscribes to the given channels, and calls
 * onEvent for every message received on any of them (including the caller's
 * own private user:{id} channel, which the server auto-subscribes). */
export function useLiveChannels(channels: string[], onEvent: (event: WsEvent) => void): void {
  const onEventRef = useRef(onEvent);
  onEventRef.current = onEvent;
  const channelsKey = channels.join(",");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) return;

    const socket = new WebSocket(`${WS_BASE_URL}/ws?token=${token}`);
    socket.onopen = () => {
      for (const channel of channelsKey.split(",").filter(Boolean)) {
        socket.send(JSON.stringify({ type: "subscribe", channel }));
      }
    };
    socket.onmessage = (event) => {
      try {
        onEventRef.current(JSON.parse(event.data) as WsEvent);
      } catch {
        // ignore malformed frames
      }
    };

    return () => socket.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [channelsKey]);
}
