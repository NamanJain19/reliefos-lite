import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  LocationConfig,
  LOCATIONS_REGISTRY,
  DEFAULT_LOCATION,
  getLocationById,
} from '../config/locationsRegistry';

interface LocationContextType {
  selectedLocation: LocationConfig;
  allLocations: LocationConfig[];
  setSelectedLocation: (location: LocationConfig | string) => void;
  isKamrupMetro: boolean;
}

const STORAGE_KEY = 'reliefos_selected_location_id';

const LocationContext = createContext<LocationContextType | undefined>(undefined);

export const LocationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedLocation, setSelectedLocationState] = useState<LocationConfig>(() => {
    try {
      const savedId = localStorage.getItem(STORAGE_KEY);
      if (savedId) {
        return getLocationById(savedId);
      }
    } catch {
      // LocalStorage unavailable in certain sandboxes
    }
    return DEFAULT_LOCATION;
  });

  const setSelectedLocation = (target: LocationConfig | string) => {
    const nextLoc = typeof target === 'string' ? getLocationById(target) : target;
    setSelectedLocationState(nextLoc);
    try {
      localStorage.setItem(STORAGE_KEY, nextLoc.id);
    } catch {
      // ignore storage write errors
    }

    // Broadcast globally to any decoupled non-React or Leaflet components
    window.dispatchEvent(
      new CustomEvent('reliefos-location-changed', {
        detail: { location: nextLoc },
      })
    );
  };

  const isKamrupMetro = selectedLocation.id === 'kamrup_metro';

  return (
    <LocationContext.Provider
      value={{
        selectedLocation,
        allLocations: LOCATIONS_REGISTRY,
        setSelectedLocation,
        isKamrupMetro,
      }}
    >
      {children}
    </LocationContext.Provider>
  );
};

export const useLocationContext = (): LocationContextType => {
  const context = useContext(LocationContext);
  if (!context) {
    // Provide graceful fallback to DEFAULT_LOCATION if rendered outside provider
    return {
      selectedLocation: DEFAULT_LOCATION,
      allLocations: LOCATIONS_REGISTRY,
      setSelectedLocation: () => {},
      isKamrupMetro: true,
    };
  }
  return context;
};
