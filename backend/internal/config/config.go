package config

import (
	"fmt"

	"os"

	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	HTTPPort string

	DatabaseURL string

	Environment string

	UpstoxBaseURL string

	UpstoxAPIKey string

	UpstoxAnalyticsToken string

	IPOSyncInterval time.Duration
}

func Load() (*Config, error) {

	_ = godotenv.Load()

	cfg := &Config{

		HTTPPort: getEnv("HTTP_PORT", "8080"),

		DatabaseURL: getEnv("DATABASE_URL", ""),

		Environment: getEnv("ENVIRONMENT", "development"),

		UpstoxBaseURL: getEnv("UPSTOX_BASE_URL", "https://api.upstox.com"),

		UpstoxAPIKey: getEnv("UPSTOX_API_KEY", ""),

		UpstoxAnalyticsToken: getEnv("UPSTOX_ANALYTICS_TOKEN", ""),

		IPOSyncInterval: getDuration("IPO_SYNC_INTERVAL", 10*time.Minute),
	}

	if cfg.DatabaseURL == "" {

		return nil, fmt.Errorf("DATABASE_URL is required")

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

	}

	return fallback

}
