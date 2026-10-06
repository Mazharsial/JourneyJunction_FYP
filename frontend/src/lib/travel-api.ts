/** Typed client for locations & travel endpoints. */
import { apiFetch } from "@/lib/api";

export interface Country {
  iso2: string;
  name: string;
  currency_code: string;
  phone_code: string;
}
export interface City {
  id: string;
  country_iso2: string;
  name: string;
  iata_code: string;
  timezone: string;
}
export interface FlightOffer {
  provider: string;
  airline: string;
  flight_number: string;
  origin_iata: string;
  destination_iata: string;
  depart_time: string;
  arrive_time: string;
  duration_minutes: number;
  stops: number;
  cabin: string;
  price_amount: number;
  price_currency: string;
}
export interface HotelOffer {
  provider: string;
  name: string;
  rating: number;
  address: string;
  amenities: string[];
  nights: number;
  price_per_night: number;
  total_amount: number;
  price_currency: string;
}
export interface CityRef {
  id: string;
  name: string;
  iata_code: string;
  country_iso2: string;
}
export interface TripOut {
  id: string;
  title: string;
  destination: CityRef;
  origin: CityRef | null;
  start_date: string;
  end_date: string;
  budget_tier: string;
  travelers: number;
  status: string;
  created_at: string;
}
export interface ItineraryDay {
  day_number: number;
  date: string;
  title: string;
  notes: string;
}
export interface VisaInfo {
  requirement: string;
  allowed_stay_days: number | null;
  notes: string;
  disclaimer: string;
}
export interface RequiredDocument {
  label: string;
  doc_type: string | null;
  status: "verified" | "not_verified" | "informational";
}
export interface TravelRequirements {
  destination_country: string;
  destination_iso2: string;
  passport_validity_months: number;
  visa: VisaInfo | null;
  required_documents: RequiredDocument[];
  documents_ready: number;
  documents_required: number;
  health: string[];
  currency_notes: string;
  customs_notes: string;
  entry_notes: string;
  emergency_number: string;
  official_source: string;
  disclaimer: string;
}
export interface TripDetail {
  trip: TripOut;
  itinerary: ItineraryDay[];
  suggested_flights: FlightOffer[];
  suggested_hotels: HotelOffer[];
  visa: VisaInfo | null;
  requirements: TravelRequirements | null;
}
export interface TripCreate {
  destination_city_id: string;
  origin_city_id?: string | null;
  start_date: string;
  end_date: string;
  budget_tier: string;
  travelers: number;
  title?: string;
}

// Public reference data
export const locationApi = {
  countries: () => apiFetch<Country[]>("/locations/countries"),
  cities: (country?: string) =>
    apiFetch<City[]>(`/locations/cities${country ? `?country=${country}` : ""}`),
};

// Authenticated travel operations (token supplied by the auth context)
export const travelApi = {
  createTrip: (token: string, data: TripCreate) =>
    apiFetch<TripOut>("/trips", { method: "POST", body: data, token }),
  listTrips: (token: string) => apiFetch<TripOut[]>("/trips", { token }),
  getTrip: (token: string, id: string) => apiFetch<TripDetail>(`/trips/${id}`, { token }),
};
