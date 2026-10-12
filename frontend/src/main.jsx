import { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API_BASE = import.meta.env.VITE_API_URL || ''
const PAGE_SIZE = 6

const STATUS_LABELS = {
  all: 'All issues',
  open: 'Open now',
  upcoming: 'Upcoming',
  closed: 'Closed',
  listed: 'Listed',
}

const MOCK_IPOS = [
  {
    id: 'shree-tnb-polymers-limited-ipo',
    symbol: 'SHREETNB',
    name: 'Shree TNB Polymers IPO',
    status: 'open',
    issue_type: 'sme',
    issue_size: 31,
    industry: 'Plastic Products',
    minimum_price: 47,
    maximum_price: 52,
    bidding_start_date: '2026-10-08',
    bidding_end_date: '2026-10-12',
    total_subscription: 12.4,
    lot_size: 2000,
    minimum_quantity: 2000,
    listing_date: '2026-10-16',
    listing_exchange: 'BSE SME',
    registrar_info: { name: 'Skyline Financial Services' },
  },
  {
    id: 'autofurnish-limited-ipo',
    symbol: 'AFLTD',
    name: 'Autofurnish Limited IPO',
    status: 'open',
    issue_type: 'sme',
    issue_size: 15,
    industry: 'Automobile Components',
    minimum_price: 41,
    maximum_price: 41,
    bidding_start_date: '2026-10-09',
    bidding_end_date: '2026-10-13',
    total_subscription: 4.8,
    lot_size: 3000,
    minimum_quantity: 6000,
    listing_date: '2026-10-19',
    listing_exchange: 'BSE SME',
  },
  {
    id: 'northern-arc-capital-ipo',
    symbol: 'NACFIN',
    name: 'Northern Arc Capital IPO',
    status: 'upcoming',
    issue_type: 'regular',
    issue_size: 500,
    industry: 'Financial Services',
    minimum_price: 462,
    maximum_price: 486,
    bidding_start_date: '2026-10-15',
    bidding_end_date: '2026-10-17',
    lot_size: 30,
    minimum_quantity: 30,
    listing_date: '2026-10-23',
    listing_exchange: 'NSE, BSE',
  },
  {
    id: 'zephyr-infra-ipo',
    symbol: 'ZEPHYR',
    name: 'Zephyr Infrastructure IPO',
    status: 'upcoming',
    issue_type: 'regular',
    issue_size: 840,
    industry: 'Construction & Engineering',
    minimum_price: 118,
    maximum_price: 124,
    bidding_start_date: '2026-10-21',
    bidding_end_date: '2026-10-23',
    lot_size: 120,
    minimum_quantity: 120,
    listing_date: '2026-10-29',
    listing_exchange: 'NSE, BSE',
  },
  {
    id: 'shree-ram-robotics-ipo',
    symbol: 'SRRTECH',
    name: 'Shree Ram Robotics IPO',
    status: 'closed',
    issue_type: 'sme',
    issue_size: 22,
    industry: 'Industrial Machinery',
    minimum_price: 87,
    maximum_price: 92,
    bidding_start_date: '2026-10-01',
    bidding_end_date: '2026-10-05',
    total_subscription: 38.6,
    lot_size: 1200,
    minimum_quantity: 1200,
    listing_date: '2026-10-10',
    listing_exchange: 'NSE SME',
    allotment_date: '2026-10-07',
  },
  {
    id: 'greenfield-diagnostics-ipo',
    symbol: 'GREENLAB',
    name: 'Greenfield Diagnostics IPO',
    status: 'listed',
    issue_type: 'regular',
    issue_size: 312,
    industry: 'Healthcare Services',
    minimum_price: 226,
    maximum_price: 238,
    listing_price: 284,
    bidding_start_date: '2026-09-22',
    bidding_end_date: '2026-09-24',
    total_subscription: 17.3,
    lot_size: 63,
    minimum_quantity: 63,
    listing_date: '2026-09-30',
    listing_exchange: 'NSE, BSE',
  },
  {
    id: 'kaveri-microfinance-ipo',
    symbol: 'KAVERI',
    name: 'Kaveri Microfinance IPO',
    status: 'listed',
    issue_type: 'regular',
    issue_size: 420,
    industry: 'Financial Services',
    minimum_price: 154,
    maximum_price: 162,
    listing_price: 171,
    bidding_start_date: '2026-09-15',
    bidding_end_date: '2026-09-18',
    total_subscription: 9.1,
    lot_size: 92,
    minimum_quantity: 92,
    listing_date: '2026-09-25',
    listing_exchange: 'NSE, BSE',
  },
  {
    id: 'meridian-foods-ipo',
    symbol: 'MERIFOOD',
    name: 'Meridian Foods India IPO',
    status: 'closed',
    issue_type: 'regular',
    issue_size: 267,
    industry: 'Food Products',
    minimum_price: 304,
    maximum_price: 318,
    bidding_start_date: '2026-09-10',
    bidding_end_date: '2026-09-12',
    total_subscription: 6.7,
    lot_size: 47,
    minimum_quantity: 47,
    listing_date: '2026-09-19',
    listing_exchange: 'NSE, BSE',
  },
]

const MOCK_HOME = {
  upcoming: MOCK_IPOS.filter((item) => item.status === 'upcoming'),
  open: MOCK_IPOS.filter((item) => item.status === 'open'),
  closed: MOCK_IPOS.filter((item) => item.status === 'closed'),
  listed: MOCK_IPOS.filter((item) => item.status === 'listed'),
}

function apiUrl(path) {
  return `${API_BASE}${path}`
}

async function getJson(path) {
  const response = await fetch(apiUrl(path))
  if (!response.ok) throw new Error(`Request failed: ${response.status}`)
  return response.json()
}

async function getAllIpos() {
  const pageSize = 100
  const firstPage = await getJson(`/api/v1/ipos?page=1&limit=${pageSize}&sort=newest`)
  const totalPages = firstPage.pagination?.pages || 1

  if (totalPages === 1) return firstPage.data || []

  const remainingPages = await Promise.all(
    Array.from({ length: totalPages - 1 }, (_, index) =>
      getJson(`/api/v1/ipos?page=${index + 2}&limit=${pageSize}&sort=newest`),
    ),
  )

  return uniqueItems([
    ...(firstPage.data || []),
    ...remainingPages.flatMap((payload) => payload.data || []),
  ])
}

function formatDate(value, withYear = false) {
  if (!value) return '—'
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    ...(withYear ? { year: 'numeric' } : {}),
  }).format(date)
}

function formatToday() {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date()).toUpperCase()
}

function formatNumericToday() {
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  }).format(new Date()).replaceAll('/', ' / ')
}

function formatTimeNow() {
  return new Intl.DateTimeFormat('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(new Date())
}

function dateParts(value) {
  if (!value) return { day: '—', month: '—', year: '—' }
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return { day: value, month: '', year: '' }
  return {
    day: new Intl.DateTimeFormat('en-IN', { day: '2-digit' }).format(date),
    month: new Intl.DateTimeFormat('en-IN', { month: 'short' }).format(date).toUpperCase(),
    year: new Intl.DateTimeFormat('en-IN', { year: 'numeric' }).format(date),
  }
}

function formatCurrency(value) {
  if (value === undefined || value === null || value === '') return '—'
  return `₹${Number(value).toLocaleString('en-IN')}`
}

function formatIssueSize(value) {
  if (value === undefined || value === null || value === '') return '—'
  return `₹${Number(value).toLocaleString('en-IN')} Cr`
}

function priceRange(item) {
  const low = item.minimum_price
  const high = item.maximum_price
  if (low === undefined && high === undefined) return '—'
  if (low === high || high === undefined) return formatCurrency(low)
  return `${formatCurrency(low)} – ${formatCurrency(high)}`
}

function uniqueItems(items) {
  return Array.from(new Map(items.map((item) => [item.id, item])).values())
}

function statusText(status) {
  return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown'
}

function StatusBadge({ status }) {
  return <span className={`status status-${status}`}>{statusText(status)}</span>
}

function Metric({ label, value, detail }) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <span className="metric-detail">{detail}</span>
    </div>
  )
}

function Logo() {
  return (
    <a className="logo" href="#top" aria-label="Augur home">
      <span className="logo-mark">A</span>
      <span className="logo-word">AUGUR</span>
      <span className="logo-index">/ 01</span>
    </a>
  )
}

function App() {
  const [items, setItems] = useState([])
  const [home, setHome] = useState(MOCK_HOME)
  const [status, setStatus] = useState('all')
  const [issueType, setIssueType] = useState('all')
  const [sort, setSort] = useState('newest')
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [apiOnline, setApiOnline] = useState(false)
  const [usingFallback, setUsingFallback] = useState(false)
  const [error, setError] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)

  async function loadData(showRefresh = false) {
    if (showRefresh) setRefreshing(true)
    else setLoading(true)
    setError('')

    try {
      const [payload, nextItems] = await Promise.all([
        getJson('/api/v1/home?limit=20'),
        getAllIpos(),
      ])
      setHome(payload)
      setItems(nextItems)
      setApiOnline(true)
      setUsingFallback(false)
      if (!selected && nextItems[0]) setSelected(nextItems[0])
    } catch (requestError) {
      setHome(MOCK_HOME)
      setItems(MOCK_IPOS)
      setApiOnline(false)
      setUsingFallback(true)
      setError(requestError instanceof Error ? requestError.message : 'Live API unavailable')
      if (!selected) setSelected(MOCK_IPOS[0])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  async function selectItem(item) {
    setSelected(item)
    setDetail(item)
    setDrawerOpen(true)
    setDetailLoading(true)
    try {
      const payload = await getJson(`/api/v1/ipos/${encodeURIComponent(item.id)}`)
      setDetail(payload)
    } catch {
      setDetail(item)
    } finally {
      setDetailLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    setPage(1)
  }, [status, issueType, sort, query])

  const filteredItems = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()
    return [...items]
      .filter((item) => status === 'all' || item.status === status)
      .filter((item) => issueType === 'all' || item.issue_type === issueType)
      .filter((item) => {
        if (!normalizedQuery) return true
        return [item.name, item.symbol, item.industry]
          .filter(Boolean)
          .some((value) => value.toLowerCase().includes(normalizedQuery))
      })
      .sort((a, b) => {
        if (sort === 'newest') return 0
        if (sort === 'listing_date') return String(a.listing_date || '').localeCompare(String(b.listing_date || ''))
        if (sort === 'bidding_start_date') return String(a.bidding_start_date || '').localeCompare(String(b.bidding_start_date || ''))
        if (sort === 'bidding_end_date') return String(a.bidding_end_date || '').localeCompare(String(b.bidding_end_date || ''))
        return String(b.bidding_start_date || '').localeCompare(String(a.bidding_start_date || ''))
      })
  }, [items, issueType, query, sort, status])

  const pages = Math.max(1, Math.ceil(filteredItems.length / PAGE_SIZE))
  const pagedItems = filteredItems.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const openCount = items.filter((item) => item.status === 'open').length
  const upcomingCount = items.filter((item) => item.status === 'upcoming').length
  const closedCount = items.filter((item) => item.status === 'closed').length
  const totalIssueSize = items
    .filter((item) => item.status === 'open')
    .reduce((sum, item) => sum + Number(item.issue_size || 0), 0)
  const activeItem = detail || selected
  const nextUpcoming = home.upcoming?.[0]
  const nextDate = dateParts(nextUpcoming?.bidding_start_date)

  return (
    <div className="app-shell" id="top">
      <header className="topbar">
        <Logo />
        <nav className="primary-nav" aria-label="Primary navigation">
          <a className="active" href="#board">Market board</a>
          <a href="#calendar">IPO calendar</a>
          <a href="#method">Methodology</a>
        </nav>
        <div className="topbar-meta">
          <span className={`api-indicator ${apiOnline ? 'is-online' : ''}`} aria-label={apiOnline ? 'API connected' : 'Using local preview'} />
          <span>{apiOnline ? 'API CONNECTED' : 'LOCAL PREVIEW'}</span>
          <span className="topbar-date">{formatToday()}</span>
        </div>
      </header>

      <main>
        <section className="hero-grid">
          <div className="hero-copy">
            <p className="kicker">Primary market / India / v1</p>
            <h1>The primary market, <em>without</em> the noise.</h1>
            <p className="hero-description">
              A live, structured view of every issue: what is open, what is next, and what happened after listing.
            </p>
            <a className="hero-link" href="#board">Explore the board <span>↘</span></a>
          </div>
          <div className="hero-panel" aria-label="Market snapshot">
            <div className="panel-heading">
              <span>Market pulse</span>
              <span className="mono">{formatNumericToday()}</span>
            </div>
            <div className="market-signal">
              <div className="signal-ring"><span>{openCount}</span></div>
              <div>
                <span className="signal-label">Issues accepting bids</span>
                <strong>Watch the live window</strong>
              </div>
            </div>
            <div className="signal-bars" aria-hidden="true">
              <i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i />
            </div>
            <div className="panel-foot">
              <span><b className="orange-dot" /> {usingFallback ? 'Local preview data' : 'Data refreshed from Augur API'}</span>
              <span className="mono">SYNC {formatTimeNow()} IST</span>
            </div>
          </div>
        </section>

        <section className="metrics-strip" aria-label="Market metrics">
          <Metric label="Open now" value={String(openCount).padStart(2, '0')} detail="bidding windows" />
          <Metric label="Up next" value={String(upcomingCount).padStart(2, '0')} detail="scheduled issues" />
          <Metric label="Active issue size" value={`₹${totalIssueSize.toLocaleString('en-IN')}`} detail="crore · open now" />
          <Metric label="Recently closed" value={String(closedCount).padStart(2, '0')} detail="awaiting allocation" />
        </section>

        {error && (
          <div className="data-notice" role="status">
            <span className="orange-dot" /> {usingFallback ? 'Showing local preview data.' : 'Live data request failed.'} <span>{error}</span>
          </div>
        )}

        <section className="board-section" id="board">
          <div className="section-heading">
            <div>
              <p className="kicker">01 / Intelligence board</p>
              <h2>Know where to look.</h2>
            </div>
            <p className="section-intro">The essential IPO signal in one scan. Select an issue to see its full timeline and application details.</p>
          </div>

          <div className="toolbar" role="toolbar" aria-label="Filter IPOs">
            <div className="filter-tabs" role="tablist" aria-label="Issue status">
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <button
                  key={value}
                  className={status === value ? 'selected' : ''}
                  onClick={() => setStatus(value)}
                  role="tab"
                  aria-selected={status === value}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="filter-tools">
              <label className="search-field">
                <span className="search-glyph">/</span>
                <span className="sr-only">Search issues</span>
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search issues" />
                <kbd>⌘ K</kbd>
              </label>
              <label className="select-field">
                <span className="sr-only">Issue type</span>
                <select value={issueType} onChange={(event) => setIssueType(event.target.value)}>
                  <option value="all">All types</option>
                  <option value="regular">Regular</option>
                  <option value="sme">SME</option>
                </select>
              </label>
              <label className="select-field">
                <span className="sr-only">Sort issues</span>
                <select value={sort} onChange={(event) => setSort(event.target.value)}>
                  <option value="newest">Newest first</option>
                  <option value="bidding_start_date">Bidding opens</option>
                  <option value="bidding_end_date">Bidding closes</option>
                  <option value="listing_date">Listing date</option>
                </select>
              </label>
              <button className="refresh-button" onClick={() => loadData(true)} disabled={refreshing} aria-label="Refresh data">
                <span className={refreshing ? 'spin' : ''}>↻</span>
              </button>
            </div>
          </div>

          <div className="board-layout">
            <div className="table-shell">
              <div className="table-meta">
                <span>{loading ? 'Reading market data…' : `${filteredItems.length} issues in view`}</span>
                <span className="mono">SORT / {sort.replaceAll('_', ' ').toUpperCase()}</span>
              </div>
              <div className="ipo-table" role="table" aria-label="IPO market board">
                <div className="table-header" role="row">
                  <span>Issue</span>
                  <span>Window</span>
                  <span>Price band</span>
                  <span>Issue size</span>
                  <span>Signal</span>
                  <span aria-hidden="true" />
                </div>
                {loading ? (
                  Array.from({ length: 4 }).map((_, index) => <div className="skeleton-row" key={index} />)
                ) : pagedItems.length ? (
                  pagedItems.map((item, index) => (
                    <div
                      className={`ipo-row ${activeItem?.id === item.id ? 'is-active' : ''}`}
                      key={item.id}
                      role="row"
                      tabIndex="0"
                      onClick={() => selectItem(item)}
                      onKeyDown={(event) => {
                        if (event.key === 'Enter' || event.key === ' ') selectItem(item)
                      }}
                    >
                      <div className="issue-cell">
                        <span className="row-index">{String((page - 1) * PAGE_SIZE + index + 1).padStart(2, '0')}</span>
                        <div>
                          <strong>{item.name}</strong>
                          <span>{item.symbol || 'SYMBOL PENDING'} <i>/</i> {item.issue_type === 'sme' ? 'SME' : 'REGULAR'}</span>
                        </div>
                      </div>
                      <div className="window-cell">
                        <strong>{formatDate(item.bidding_start_date)}</strong>
                        <span>to {formatDate(item.bidding_end_date)}</span>
                      </div>
                      <div className="price-cell">{priceRange(item)}</div>
                      <div className="size-cell">{formatIssueSize(item.issue_size)}</div>
                      <div className="signal-cell">
                        <StatusBadge status={item.status} />
                        {item.total_subscription ? <span className="subscription">{item.total_subscription}× subscribed</span> : <span className="subscription">Tracking</span>}
                      </div>
                      <span className="row-arrow">↗</span>
                    </div>
                  ))
                ) : (
                  <div className="empty-state">
                    <strong>No issues match this view.</strong>
                    <span>Try removing a filter or searching another company.</span>
                  </div>
                )}
              </div>
              <div className="pagination">
                <span>Showing {filteredItems.length ? (page - 1) * PAGE_SIZE + 1 : 0}–{Math.min(page * PAGE_SIZE, filteredItems.length)} of {filteredItems.length}</span>
                <div>
                  <button onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>←</button>
                  <span className="page-count">{String(page).padStart(2, '0')} / {String(pages).padStart(2, '0')}</span>
                  <button onClick={() => setPage((current) => Math.min(pages, current + 1))} disabled={page === pages}>→</button>
                </div>
              </div>
            </div>

            <aside className="calendar-card" id="calendar">
              <div className="card-topline"><span>Next on the tape</span><span className="mono">OCT / 26</span></div>
              <div className="calendar-date"><strong>{nextDate.day}</strong><span>{nextDate.month}<br />{nextDate.year}</span></div>
              <h3>{nextUpcoming?.name || 'No upcoming issue'}</h3>
              <p>{nextUpcoming?.industry || 'Upcoming IPO'} · {nextUpcoming ? priceRange(nextUpcoming) : 'Details pending'}</p>
              <div className="calendar-rule" />
              <div className="calendar-detail"><span>Bidding window</span><strong>{nextUpcoming ? `${formatDate(nextUpcoming.bidding_start_date)} → ${formatDate(nextUpcoming.bidding_end_date)}` : '—'}</strong></div>
              <div className="calendar-detail"><span>Issue type</span><strong>{nextUpcoming?.issue_type === 'sme' ? 'SME' : 'Regular'}</strong></div>
              <button className="text-button" onClick={() => nextUpcoming && selectItem(nextUpcoming)}>View issue details <span>↗</span></button>
            </aside>
          </div>
        </section>

        <section className="method-section" id="method">
          <div className="method-stamp">AUGUR<br /><span>DATA NOTE</span></div>
          <div>
            <p className="kicker">02 / Read the signal</p>
            <h2>Less noise.<br /><em>More context.</em></h2>
          </div>
          <p className="method-copy">Augur normalizes IPO data from Upstox into a stable feed — separating discovery, hydration, storage, and the decision surface you see here.</p>
          <div className="method-status"><span className={`api-indicator ${apiOnline ? 'is-online' : ''}`} /> {usingFallback ? 'Showing local preview data' : 'Connected to Augur API'}<br /><span>Source: Upstox / API v1</span></div>
        </section>
      </main>

      <footer className="footer">
        <Logo />
        <span>Primary market intelligence, in plain sight.</span>
        <span className="mono">BUILD 0.1.0 / {apiOnline ? 'LIVE' : 'DEMO'}</span>
      </footer>

      {drawerOpen && activeItem && (
        <div className="drawer-backdrop" onClick={() => setDrawerOpen(false)}>
          <aside className="detail-drawer" onClick={(event) => event.stopPropagation()} aria-label="IPO details">
            <button className="close-drawer" onClick={() => setDrawerOpen(false)} aria-label="Close details">×</button>
            <div className="drawer-head">
              <span className="kicker">Issue dossier / {activeItem.issue_type === 'sme' ? 'SME' : 'Regular'}</span>
              <StatusBadge status={activeItem.status} />
              <h2>{activeItem.name}</h2>
              <p>{activeItem.symbol || 'SYMBOL PENDING'} · {activeItem.industry || 'Industry not disclosed'}</p>
            </div>
            {detailLoading ? <div className="drawer-loading">Loading issue detail<span>...</span></div> : (
              <>
                <div className="drawer-highlight"><span>Price band</span><strong>{priceRange(activeItem)}</strong><span>Minimum application / {formatCurrency(Number(activeItem.maximum_price || activeItem.minimum_price || 0) * Number(activeItem.minimum_quantity || activeItem.lot_size || 0))}</span></div>
                <div className="detail-grid">
                  <div><span>Issue size</span><strong>{formatIssueSize(activeItem.issue_size)}</strong></div>
                  <div><span>Lot size</span><strong>{activeItem.lot_size || '—'}</strong></div>
                  <div><span>Bid opens</span><strong>{formatDate(activeItem.bidding_start_date, true)}</strong></div>
                  <div><span>Bid closes</span><strong>{formatDate(activeItem.bidding_end_date, true)}</strong></div>
                  <div><span>Listing exchange</span><strong>{activeItem.listing_exchange || '—'}</strong></div>
                  <div><span>Subscription</span><strong>{activeItem.total_subscription ? `${activeItem.total_subscription}×` : 'Tracking'}</strong></div>
                </div>
                <div className="timeline">
                  <div className="drawer-section-label">Timeline</div>
                  {[
                    ['Bidding opens', activeItem.bidding_start_date],
                    ['Bidding closes', activeItem.bidding_end_date],
                    ['Allotment date', activeItem.allotment_date || activeItem.timeline?.allotment_date],
                    ['Listing date', activeItem.listing_date || activeItem.timeline?.listing_date],
                  ].map(([label, date], index) => (
                    <div className={`timeline-row ${date ? 'has-date' : ''}`} key={label}>
                      <span className="timeline-marker">{date ? '●' : '○'}</span>
                      <span>{label}</span>
                      <strong>{formatDate(date, true)}</strong>
                      {index < 3 && <i />}
                    </div>
                  ))}
                </div>
                {activeItem.registrar_info?.name && <div className="registrar"><span>Registrar</span><strong>{activeItem.registrar_info.name}</strong></div>}
              </>
            )}
          </aside>
        </div>
      )}
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
