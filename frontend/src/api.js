export async function fetchTrips() {
  const res = await fetch('/api/trips')
  if (!res.ok) throw new Error('Failed to fetch trips')
  return res.json()
}

export async function createTrip(payload) {
  const res = await fetch('/api/trips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to create trip')
  }
  return res.json()
}

export async function fetchItinerary(tripName) {
  const res = await fetch(`/api/trips/${encodeURIComponent(tripName)}/itinerary`)
  if (!res.ok) throw new Error('Failed to fetch itinerary')
  return res.json()
}

export async function addItineraryItem(tripName, payload) {
  const res = await fetch(`/api/trips/${encodeURIComponent(tripName)}/itinerary`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.error || 'Failed to add itinerary item')
  }
}
