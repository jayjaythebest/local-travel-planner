import { useEffect, useMemo, useState } from 'react'
import { addItineraryItem, createTrip, fetchItinerary, fetchTrips } from './api'

const countries = ['日本 (Japan)', '美國 (USA)', '韓國 (South Korea)', '台灣 (Taiwan)', '泰國 (Thailand)']

export default function App() {
  const [trips, setTrips] = useState([])
  const [selectedTrip, setSelectedTrip] = useState('')
  const [itinerary, setItinerary] = useState([])
  const [error, setError] = useState('')

  const [newTrip, setNewTrip] = useState({
    name: '',
    startDate: '',
    endDate: '',
    country: countries[0]
  })

  const [newItem, setNewItem] = useState({
    日期: '',
    開始時間: '',
    結束時間: '',
    活動: '',
    地圖連結: '',
    備註: ''
  })

  const selectedMeta = useMemo(
    () => trips.find((trip) => trip['名稱'] === selectedTrip),
    [trips, selectedTrip]
  )

  async function refreshTrips() {
    try {
      const data = await fetchTrips()
      setTrips(data)
      if (!selectedTrip && data.length > 0) {
        setSelectedTrip(data[0]['名稱'])
      }
    } catch (e) {
      setError(e.message)
    }
  }

  async function refreshItinerary(tripName) {
    if (!tripName) return
    try {
      const data = await fetchItinerary(tripName)
      setItinerary(data)
    } catch (e) {
      setError(e.message)
    }
  }

  useEffect(() => {
    refreshTrips()
  }, [])

  useEffect(() => {
    refreshItinerary(selectedTrip)
  }, [selectedTrip])

  async function onCreateTrip(e) {
    e.preventDefault()
    setError('')
    try {
      await createTrip(newTrip)
      setNewTrip({ name: '', startDate: '', endDate: '', country: countries[0] })
      await refreshTrips()
      setSelectedTrip(newTrip.name)
    } catch (err) {
      setError(err.message)
    }
  }

  async function onAddItem(e) {
    e.preventDefault()
    setError('')
    try {
      await addItineraryItem(selectedTrip, newItem)
      setNewItem({ 日期: '', 開始時間: '', 結束時間: '', 活動: '', 地圖連結: '', 備註: '' })
      await refreshItinerary(selectedTrip)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="layout">
      <aside>
        <h1>旅程管理</h1>
        <select value={selectedTrip} onChange={(e) => setSelectedTrip(e.target.value)}>
          {trips.map((trip) => (
            <option key={trip['名稱']} value={trip['名稱']}>
              {trip['名稱']}
            </option>
          ))}
        </select>

        <form onSubmit={onCreateTrip}>
          <h2>新增旅程</h2>
          <input placeholder="旅程名稱" value={newTrip.name} onChange={(e) => setNewTrip({ ...newTrip, name: e.target.value })} />
          <input type="date" value={newTrip.startDate} onChange={(e) => setNewTrip({ ...newTrip, startDate: e.target.value })} />
          <input type="date" value={newTrip.endDate} onChange={(e) => setNewTrip({ ...newTrip, endDate: e.target.value })} />
          <select value={newTrip.country} onChange={(e) => setNewTrip({ ...newTrip, country: e.target.value })}>
            {countries.map((country) => (
              <option key={country} value={country}>{country}</option>
            ))}
          </select>
          <button type="submit">建立</button>
        </form>
      </aside>

      <section>
        <h2>{selectedTrip || '尚未選擇旅程'}</h2>
        {selectedMeta && (
          <p>
            {selectedMeta['開始日期']} ~ {selectedMeta['結束日期']} / {selectedMeta['國家']}
          </p>
        )}

        <form onSubmit={onAddItem}>
          <h3>新增行程（沿用同一個 Google Sheet 欄位）</h3>
          <input type="date" value={newItem['日期']} onChange={(e) => setNewItem({ ...newItem, 日期: e.target.value })} />
          <input placeholder="開始時間 HH:MM" value={newItem['開始時間']} onChange={(e) => setNewItem({ ...newItem, 開始時間: e.target.value })} />
          <input placeholder="結束時間 HH:MM" value={newItem['結束時間']} onChange={(e) => setNewItem({ ...newItem, 結束時間: e.target.value })} />
          <input placeholder="活動" value={newItem['活動']} onChange={(e) => setNewItem({ ...newItem, 活動: e.target.value })} />
          <input placeholder="地圖連結" value={newItem['地圖連結']} onChange={(e) => setNewItem({ ...newItem, 地圖連結: e.target.value })} />
          <input placeholder="備註" value={newItem['備註']} onChange={(e) => setNewItem({ ...newItem, 備註: e.target.value })} />
          <button type="submit" disabled={!selectedTrip}>新增活動</button>
        </form>

        {error && <p className="error">{error}</p>}

        <table>
          <thead>
            <tr>
              <th>日期</th>
              <th>開始</th>
              <th>結束</th>
              <th>活動</th>
              <th>備註</th>
            </tr>
          </thead>
          <tbody>
            {itinerary.map((item, idx) => (
              <tr key={`${item['日期']}-${item['開始時間']}-${idx}`}>
                <td>{item['日期']}</td>
                <td>{item['開始時間']}</td>
                <td>{item['結束時間']}</td>
                <td>{item['活動']}</td>
                <td>{item['備註']}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  )
}
