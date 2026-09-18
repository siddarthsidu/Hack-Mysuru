import { useEffect, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix Leaflet marker icons when used with Vite
delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const MYSURU_CENTER = [12.2958, 76.6394];

function MapClickHandler({ onLocationSelect }) {
  useMapEvents({
    click(event) {
      onLocationSelect({
        latitude: event.latlng.lat,
        longitude: event.latlng.lng,
      });
    },
  });

  return null;
}

export default function LocationPicker({
  latitude,
  longitude,
  onLocationChange,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [locationError, setLocationError] = useState("");

  const hasLocation =
    latitude !== null &&
    latitude !== undefined &&
    longitude !== null &&
    longitude !== undefined;

  const position = hasLocation
    ? [latitude, longitude]
    : MYSURU_CENTER;

  const selectLocation = (lat, lon) => {
    onLocationChange({
      latitude: Number(lat),
      longitude: Number(lon),
    });

    setLocationError("");
  };

  const useCurrentLocation = () => {
    setLocationError("");

    if (!navigator.geolocation) {
      setLocationError(
        "Your browser does not support location access."
      );
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (location) => {
        selectLocation(
          location.coords.latitude,
          location.coords.longitude
        );
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setLocationError(
            "Location permission was denied. Please allow location access or select a location on the map."
          );
        } else {
          setLocationError(
            "Unable to get your current location. Please select a location on the map."
          );
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );
  };

  const searchLocation = async (event) => {
    event.preventDefault();

    if (!searchQuery.trim()) {
      setLocationError("Enter an address or place to search.");
      return;
    }

    setSearching(true);
    setLocationError("");

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=in&q=${encodeURIComponent(
          searchQuery
        )}`
      );

      if (!response.ok) {
        throw new Error("Search request failed.");
      }

      const results = await response.json();

      if (!results.length) {
        setLocationError(
          "Location not found. Try a nearby landmark, road, or area name."
        );
        return;
      }

      const result = results[0];

      selectLocation(result.lat, result.lon);
    } catch (error) {
      setLocationError(
        "Unable to search for that location right now. You can select it on the map instead."
      );
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="location-picker">
      <div className="location-picker-header">
        <div>
          <h3>📍 Where is the problem?</h3>
          <p>
            Select the location of the civic issue so we can route
            your complaint to the responsible authority.
          </p>
        </div>
      </div>

      <div className="location-actions">
        <button
          type="button"
          className="location-action-button"
          onClick={useCurrentLocation}
        >
          📍 Use My Current Location
        </button>
      </div>

      <form
        className="location-search"
        onSubmit={searchLocation}
      >
        <input
          type="text"
          value={searchQuery}
          onChange={(event) =>
            setSearchQuery(event.target.value)
          }
          placeholder="Search address, road, area or landmark"
        />

        <button
          type="submit"
          disabled={searching}
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </form>

      <div className="map-wrapper">
        <MapContainer
          center={position}
          zoom={13}
          scrollWheelZoom={true}
          style={{
            width: "100%",
            height: "360px",
          }}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <MapClickHandler
            onLocationSelect={({ latitude, longitude }) =>
              selectLocation(latitude, longitude)
            }
          />

          {hasLocation && <Marker position={position} />}
        </MapContainer>
      </div>

      <div className="location-instruction">
        <span>🗺️</span>
        <span>
          Click anywhere on the map to select the exact location.
        </span>
      </div>

      {hasLocation && (
        <div className="selected-location">
          <span className="selected-location-icon">✓</span>

          <div>
            <strong>Location selected</strong>
            <p>
              Your location will be used to determine the
              responsible authority.
            </p>
          </div>
        </div>
      )}

      {locationError && (
        <div className="location-error">
          {locationError}
        </div>
      )}
    </div>
  );
}