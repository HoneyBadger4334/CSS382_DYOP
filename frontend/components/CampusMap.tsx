"use client";

import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { colors, severity as sev } from "@/lib/tokens";

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
        const s = sev[pin.severity] ?? sev.medium;
        return (
          <CircleMarker
            key={pin.id}
            center={pin.coordinates}
            radius={pin.id === "test-week7" ? 10 : 14}
            pathOptions={{
              color: s.pin,
              fillColor: s.pin,
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
                  <strong style={{ fontSize: 14, color: colors.bgBase }}>
                    {pin.incident_type}
                  </strong>
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      color: "#fff",
                      background: s.pin,
                      borderRadius: 4,
                      padding: "2px 6px",
                      marginLeft: 8,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {pin.severity.toUpperCase()}
                  </span>
                </div>

                <div style={{ fontSize: 12, color: colors.textDimmer, marginBottom: 6 }}>
                  {pin.building_name} · {formatTime(pin.published)}
                </div>

                <div
                  style={{
                    fontSize: 12,
                    color: colors.bgBase,
                    background: "#f8fafc",
                    borderRadius: 4,
                    padding: "6px 8px",
                    marginBottom: 6,
                  }}
                >
                  {pin.recommended_action}
                </div>

                <details style={{ fontSize: 11, color: colors.textFaint }}>
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
