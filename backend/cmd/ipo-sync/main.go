// cmd/ipo-sync/main.go
package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/drunktrader/ipo-checker/internal/config"
	"github.com/drunktrader/ipo-checker/internal/db"
	"github.com/drunktrader/ipo-checker/internal/ipo"
	"github.com/drunktrader/ipo-checker/internal/models"
	"github.com/drunktrader/ipo-checker/internal/upstox"
)

func main() {
	log.SetFlags(log.LstdFlags | log.Lmicroseconds)

	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	gormDB, err := db.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("db: %v", err)
	}
	if err := db.RunMigrations(gormDB, "migrations"); err != nil {
		log.Fatalf("migrations: %v", err)
	}

	// Market-hours guard at the CLI layer too: a clean exit code 0 with a
	// log line is the right behavior for cron.
	if !ipo.IsMarketHours(time.Now()) {
		log.Println("ipo-sync: outside market hours (08-18 IST), proceeding anyway")
	}

	if cfg.UpstoxAnalyticsToken == "" {
		log.Fatalf("UPSTOX_ANALYTICS_TOKEN is required")
	}

	client := upstox.NewClient(cfg.UpstoxAnalyticsToken)
	repo := models.NewIPORepository(gormDB)
	engine := ipo.NewEngine(cfg, repo, client, ipo.DefaultSyncOptions())

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	res, err := engine.Run(ctx)
	if err != nil {
		log.Printf("ipo-sync: run finished with error: %v", err)
	}

	dur := res.EndedAt.Sub(res.StartedAt)
	log.Printf("ipo-sync: done in %s created=%d updated=%d skipped=%d errors=%d",
		dur, res.Created, res.Updated, res.Skipped, res.Errors)

	// Non-zero exit if anything errored, so cron / monitoring notices.
	if res.Errors > 0 || err != nil {
		os.Exit(1)
	}
}
