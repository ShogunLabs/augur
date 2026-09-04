package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type HealthHandler struct {
	startTime time.Time
}

func NewHealthHandler() *HealthHandler {
	return &HealthHandler{startTime: time.Now()}
}

func (h *HealthHandler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":         "ok",
		"uptime_seconds": int64(time.Since(h.startTime).Seconds()),
		"timestamp":      time.Now().Format(time.RFC3339),
	})
}
