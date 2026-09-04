
package api



import (

	"net/http"

	"strconv"



	"github.com/drunktrader/ipo-checker/internal/models"

	"github.com/gin-gonic/gin"

)



type IPOHandler struct {

	repo *models.IPORepository

}



func NewIPOHandler(repo *models.IPORepository) *IPOHandler {

	return &IPOHandler{repo: repo}

}



func (h *IPOHandler) Register(rg *gin.RouterGroup) {

	rg.GET("/ipos", h.List)

	rg.GET("/ipos/:id", h.Get)

	rg.GET("/ipos/:id/gmp", h.LatestGMP)

	rg.GET("/ipos/:id/gmp/history", h.GMPHistory)

}



func (h *IPOHandler) List(c *gin.Context) {

	opts := models.ListOptions{

		Status:    c.Query("status"),

		Registrar: c.Query("registrar"),

		Search:    c.Query("q"),

	}

	if v := c.Query("page"); v != "" {

		opts.Page, _ = strconv.Atoi(v)

	}

	if v := c.Query("page_size"); v != "" {

		opts.PageSize, _ = strconv.Atoi(v)

	}



	ipos, total, err := h.repo.List(opts)

	if err != nil {

		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error", "detail": err.Error()})

		return

	}

	page := opts.Page

	if page < 1 {

		page = 1

	}

	pageSize := opts.PageSize

	if pageSize < 1 {

		pageSize = 20

	}

	c.JSON(http.StatusOK, gin.H{

		"data": ipos,

		"meta": gin.H{

			"page":      page,

			"page_size": pageSize,

			"total":     total,

		},

	})

}



func (h *IPOHandler) Get(c *gin.Context) {

	id, err := strconv.ParseUint(c.Param("id"), 10, 64)

	if err != nil {

		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})

		return

	}

	ipo, err := h.repo.GetByID(uint(id))

	if err != nil {

		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error", "detail": err.Error()})

		return

	}

	if ipo == nil {

		c.JSON(http.StatusNotFound, gin.H{"error": "ipo not found"})

		return

	}

	c.JSON(http.StatusOK, ipo)

}



func (h *IPOHandler) LatestGMP(c *gin.Context) {

	id, err := strconv.ParseUint(c.Param("id"), 10, 64)

	if err != nil {

		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})

		return

	}

	gmp, err := h.repo.GetLatestGMP(uint(id))

	if err != nil {

		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error", "detail": err.Error()})

		return

	}

	if gmp == nil {

		c.JSON(http.StatusNotFound, gin.H{"error": "no gmp data yet"})

		return

	}

	c.JSON(http.StatusOK, gmp)

}



func (h *IPOHandler) GMPHistory(c *gin.Context) {

	id, err := strconv.ParseUint(c.Param("id"), 10, 64)

	if err != nil {

		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid id"})

		return

	}

	limit := 100

	if v := c.Query("limit"); v != "" {

		limit, _ = strconv.Atoi(v)

	}

	rows, err := h.repo.GetGMPHistory(uint(id), limit)

	if err != nil {

		c.JSON(http.StatusInternalServerError, gin.H{"error": "db error", "detail": err.Error()})

		return

	}

	c.JSON(http.StatusOK, gin.H{"data": rows})

}

