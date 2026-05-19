"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export interface AlertPin {
  id: string;
  raw_text: string;
  building_name: string;
  incident_type: string;
  severity: "low" | "medium" | "high";
  recommended_action: string;
  coordinates: [number, number];
  published: string;
}

const SEVERITY_COLOR: Record<string, string> = {
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#22c55e",
};

const SEVERITY_LABEL: Record<string, string> = {
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

// UW Bothell campus center and bounding box
const CENTER: [number, number] = [47.7594, -122.1903];
const BOUNDS: [[number, number], [number, number]] = [
  [47.753, -122.198],
  [47.766, -122.182],
];

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function CampusMap({ alerts }: { alerts: AlertPin[] }) {
  return (
    <MapContainer
      center={CENTER}
      zoom={16}
      maxBounds={BOUNDS}
      maxBoundsViscosity={0.8}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        maxZoom={19}
      />

      {alerts.map((pin) => {
        const color = SEVERITY_COLOR[pin.severity] ?? SEVERITY_COLOR.medium;
        return (
          <CircleMarker
            key={pin.id}
            center={pin.coordinates}
            radius={pin.id === "test-week7" ? 10 : 14}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.85,
              weight: 2,
            }}
          >
            <Popup>
              <div style={{ padding: "10px 12px", minWidth: 220 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    marginBottom: 6,
                  }}
                >
                  <strong style={{ fontSize: 14, color: "#0f172a" }}>
                    {pin.incident_type}
                  </strong>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: "#fff",
                      background: color,
                      borderRadius: 4,
                      padding: "2px 6px",
                      marginLeft: 8,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {SEVERITY_LABEL[pin.severity] ?? pin.severity.toUpperCase()}
                  </span>
                </div>

                <div style={{ fontSize: 12, color: "#475569", marginBottom: 6 }}>
                  {pin.building_name} · {formatTime(pin.published)}
                </div>

                <div
                  style={{
                    fontSize: 12,
                    color: "#1e293b",
                    background: "#f8fafc",
                    borderRadius: 4,
                    padding: "6px 8px",
                    marginBottom: 6,
                  }}
                >
                  {pin.recommended_action}
                </div>

                <details style={{ fontSize: 11, color: "#64748b" }}>
                  <summary style={{ cursor: "pointer" }}>Raw alert</summary>
                  <p style={{ marginTop: 4 }}>{pin.raw_text}</p>
                </details>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
