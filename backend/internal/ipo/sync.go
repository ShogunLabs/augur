// internal/ipo/sync.go
package ipo

import (
	"context"
	"errors"
	"log"
	"sync"
	"time"

	"github.com/drunktrader/ipo-checker/internal/config"
	"github.com/drunktrader/ipo-checker/internal/models"
	"github.com/drunktrader/ipo-checker/internal/upstox"
)

// Statuses is the full upstox status taxonomy we sync.
var Statuses = []string{"upcoming", "open", "closed", "listed"}

// IssueTypes is what we keep separately in the database.
var IssueTypes = []string{"regular"}

// SyncResult is the per-run summary written to logs and returned.
type SyncResult struct {
	Created   int
	Updated   int
	Skipped   int
	Errors    int
	StartedAt time.Time
	EndedAt   time.Time
}

// Clock is indirection over time.Now, useful for tests.
type Clock interface {
	Now() time.Time
}

type realClock struct{}

func (realClock) Now() time.Time { return time.Now() }

// SyncOptions configures a single sync run.
type SyncOptions struct {
	// FreshSkipDuration: skip per-IPO detail fetch if the row was last
	// touched within this window. For a 30-min cron, 25m is a good default.
	FreshSkipDuration time.Duration
	// DetailSleep: pause between per-IPO detail calls to be polite to upstox.
	DetailSleep time.Duration
	// MaxDetailCalls: hard cap on detail calls per run; protects us from
	// runaway pages or a misbehaving cron.
	MaxDetailCalls int
	// PageSize: how many rows to request per list call.
	PageSize int
}

// DefaultSyncOptions returns the production defaults discussed.
func DefaultSyncOptions() SyncOptions {
	return SyncOptions{
		FreshSkipDuration: 25 * time.Minute,
		DetailSleep:       200 * time.Millisecond,
		MaxDetailCalls:    30,
		PageSize:          50,
	}
}

// Engine is the sync engine; it owns no goroutines of its own.
type Engine struct {
	cfg     *config.Config
	repo    *models.IPORepository
	client  *upstox.Client
	clock   Clock
	options SyncOptions
}

// NewEngine wires the engine with all collaborators.
func NewEngine(cfg *config.Config, repo *models.IPORepository, client *upstox.Client, opts SyncOptions) *Engine {
	return &Engine{
		cfg:     cfg,
		repo:    repo,
		client:  client,
		clock:   realClock{},
		options: opts,
	}
}

// IsMarketHours reports whether the given time (in IST) is between 08:00 and
// 18:00 inclusive of 08:00, exclusive of 18:00.
func IsMarketHours(t time.Time) bool {
	ist := time.FixedZone("IST", 5*3600+30*60)
	local := t.In(ist)
	h := local.Hour()
	return h >= 8 && h < 18
}

// Run executes one full sync pass. Returns a summary; never panics.
func (e *Engine) Run(ctx context.Context) (SyncResult, error) {
	res := SyncResult{StartedAt: e.clock.Now()}
	defer func() { res.EndedAt = e.clock.Now() }()

	// Market-hours guard. The caller (CLI) also checks, but we re-check here
	// so the engine is safe to call from any path.
	if !IsMarketHours(e.clock.Now()) {
		log.Println("[sync] outside market hours (08-18 IST), nothing to do")
		return res, nil
	}

	if e.client == nil {
		return res, errors.New("sync: upstox client is nil")
	}
	if e.repo == nil {
		return res, errors.New("sync: repository is nil")
	}

	var mu sync.Mutex
	detailCalls := 0

	for _, status := range Statuses {
		for _, issueType := range IssueTypes {
			page := 1
			for {
				if ctx.Err() != nil {
					return res, ctx.Err()
				}

				list, err := e.client.GetIPOs(status, issueType, page, e.options.PageSize)
				if err != nil {
					log.Printf("[sync] list error status=%s issueType=%s page=%d: %v", status, issueType, page, err)
					mu.Lock()
					res.Errors++
					mu.Unlock()
					break
				}
				if list == nil || len(list.Data) == 0 {
					break
				}

				for _, item := range list.Data {
					if ctx.Err() != nil {
						return res, ctx.Err()
					}

					mu.Lock()
					if detailCalls >= e.options.MaxDetailCalls {
						mu.Unlock()
						log.Printf("[sync] hit MaxDetailCalls=%d, ending run early", e.options.MaxDetailCalls)
						return res, nil
					}
					detailCalls++
					mu.Unlock()

					created, updated, skipped, err := e.syncOne(ctx, item, status, issueType)
					mu.Lock()
					res.Created += boolToInt(created)
					res.Updated += boolToInt(updated)
					res.Skipped += boolToInt(skipped)
					if err != nil {
						res.Errors++
					}
					mu.Unlock()

					if e.options.DetailSleep > 0 {
						select {
						case <-time.After(e.options.DetailSleep):
						case <-ctx.Done():
							return res, ctx.Err()
						}
					}
				}

				// Stop paging when the API returns a short page; we already
				// have everything for this status+issueType.
				if len(list.Data) < e.options.PageSize {
					break
				}
				page++
			}
		}
	}

	return res, nil
}

// syncOne handles a single upstox IPO row: freshness check, detail fetch,
// upsert. Returns (created, updated, skipped, err) flags.
func (e *Engine) syncOne(ctx context.Context, item upstox.IPOSummary, status, issueType string) (created, updated, skipped bool, err error) { // Freshness check: look up the local row by upstox id.
	_ = ctx
	existing, err := e.repo.GetByExternalID(item.ID)
	if err != nil {
		return false, false, false, err
	}
	if existing != nil {
		cutoff := e.clock.Now().Add(-e.options.FreshSkipDuration)
		lastSeen := e.lastSeenAt(existing)
		if !lastSeen.IsZero() && lastSeen.After(cutoff) {
			return false, false, true, nil
		}
	}

	details, err := e.client.GetIPODetails(item.ID)
	if err != nil {
		log.Printf("[sync] details error id=%s: %v", item.ID, err)
		return false, false, false, err
	}
	if details == nil {
		return false, false, false, errors.New("upstox: nil details")
	}

	// UpsertFromUpstoxDetails takes *upstox.IPODetails; the response wraps it
	// in a value, so we hand off the address.
	wasCreated, err := e.repo.UpsertFromUpstoxDetails(&details.Data)
	if err != nil {
		return false, false, false, err
	}
	if wasCreated {
		return true, false, false, nil
	}
	return false, true, false, nil
}

// lastSeenAt returns the most recent timestamp we have on file for an IPO,
// preferring SourceUpdatedAt (the upstream truth) and falling back to
// UpdatedAt (our local write time).
func (e *Engine) lastSeenAt(ipo *models.IPO) time.Time {
	// IPO has no per-source timestamp; UpdatedAt is the only signal we have.
	return ipo.UpdatedAt
}

func boolToInt(b bool) int {
	if b {
		return 1
	}
	return 0
}
