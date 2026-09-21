package config

import (
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	HTTPPort             string
	DatabaseURL          string
	Environment          string
	UpstoxBaseURL        string
	UpstoxAPIKey         string
	UpstoxAnalyticsToken string
	IPOSyncInterval      time.Duration
}

func Load() (*Config, error) {
	// Only load .env in development environment
	if os.Getenv("ENVIRONMENT") == "development" {
		if err := godotenv.Load(); err != nil {
			log.Printf("INFO: .env file not found, using environment variables only")
		}
	}

	cfg := &Config{
		HTTPPort:             getEnv("HTTP_PORT", "8080"),
		DatabaseURL:          getEnv("DATABASE_URL", ""),
		Environment:          getEnv("ENVIRONMENT", "development"),
		UpstoxBaseURL:        getEnv("UPSTOX_BASE_URL", "https://api.upstox.com"),
		UpstoxAPIKey:         getEnv("UPSTOX_API_KEY", ""),
		UpstoxAnalyticsToken: getEnv("UPSTOX_ANALYTICS_TOKEN", ""),
		IPOSyncInterval:      getDuration("IPO_SYNC_INTERVAL", 10*time.Minute),
	}

	// Validate required fields
	var missing []string
	if cfg.DatabaseURL == "" {
		missing = append(missing, "DATABASE_URL")
	}
	if cfg.UpstoxAnalyticsToken == "" {
		missing = append(missing, "UPSTOX_ANALYTICS_TOKEN")
	}

	if len(missing) > 0 {
		return nil, fmt.Errorf("missing required configuration: %v", missing)
	}

	// Validate token format (expect non-empty and no whitespace)
	if strings.TrimSpace(cfg.UpstoxAnalyticsToken) == "" {
		return nil, fmt.Errorf("UPSTOX_ANALYTICS_TOKEN contains only whitespace")
	}

	// Warn if token format looks suspicious
	if !strings.HasPrefix(cfg.UpstoxAnalyticsToken, "Bearer_") && 
	   !strings.HasPrefix(cfg.UpstoxAnalyticsToken, "eyJ") {
		log.Printf("WARNING: UPSTOX_ANALYTICS_TOKEN format may be invalid (expected Bearer_ or JWT prefix)")
	}

	return cfg, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getDuration(key string, fallback time.Duration) time.Duration {
	if v := os.Getenv(key); v != "" {
		if d, err := time.ParseDuration(v); err == nil {
			return d
		}
		log.Printf("WARNING: invalid duration for %s: %q, using default %v", key, v, fallback)
	}
	return fallback
}
