package models

import (
	"errors"

	"gorm.io/gorm"
	"github.com/drunktrader/ipo-checker/internal/upstox"
	"time"
)

type IPORepository struct {
	db *gorm.DB
}

func NewIPORepository(db *gorm.DB) *IPORepository {

	return &IPORepository{db: db}

}

// ListOptions filters and paginates IPO list queries.

type ListOptions struct {
	Status string

	Registrar string

	Search string

	Page int

	PageSize int
}

func (r *IPORepository) List(opts ListOptions) ([]IPO, int64, error) {
	if opts.Page < 1 {
		opts.Page = 1
	}

	if opts.PageSize < 1 || opts.PageSize > 100 {
		opts.PageSize = 20
	}

	// Cap maximum page to prevent DoS via deep pagination
	const maxPage = 1000
	if opts.Page > maxPage {
		opts.Page = maxPage
	}

	q := r.db.Model(&IPO{})

	if opts.Status != "" {
		q = q.Where("status = ?", opts.Status)
	}

	if opts.Registrar != "" {
		q = q.Where("registrar = ?", opts.Registrar)
	}

	if opts.Search != "" {
		like := "%" + opts.Search + "%"
		q = q.Where("name ILIKE ? OR symbol ILIKE ? OR isin ILIKE ?", like, like, like)
	}

	var total int64

	if err := q.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	var ipos []IPO

	if err := q.Order("bidding_start DESC NULLS LAST, name ASC").
		Offset((opts.Page - 1) * opts.PageSize).
		Limit(opts.PageSize).
		Find(&ipos).Error; err != nil {
		return nil, 0, err
	}

	return ipos, total, nil
}

func (r *IPORepository) GetByID(id uint) (*IPO, error) {

	var ipo IPO

	if err := r.db.First(&ipo, id).Error; err != nil {

		if errors.Is(err, gorm.ErrRecordNotFound) {

			return nil, nil

		}

		return nil, err

	}

	return &ipo, nil

}

func (r *IPORepository) GetByExternalID(externalID string) (*IPO, error) {

	var ipo IPO

	if err := r.db.Where("external_id = ?", externalID).First(&ipo).Error; err != nil {

		if errors.Is(err, gorm.ErrRecordNotFound) {

			return nil, nil

		}

		return nil, err

	}

	return &ipo, nil

}

// GetLatestGMP returns the most recent GMP snapshot for the given IPO.

func (r *IPORepository) GetLatestGMP(ipoID uint) (*IPOGMP, error) {

	var gmp IPOGMP

	if err := r.db.Where("ipo_id = ?", ipoID).
		Order("fetched_at DESC").
		First(&gmp).Error; err != nil {

		if errors.Is(err, gorm.ErrRecordNotFound) {

			return nil, nil

		}

		return nil, err

	}

	return &gmp, nil

}

// GetGMPHistory returns the last N GMP snapshots for trend views.

func (r *IPORepository) GetGMPHistory(ipoID uint, limit int) ([]IPOGMPHistory, error) {

	if limit < 1 || limit > 500 {

		limit = 100

	}

	var rows []IPOGMPHistory

	if err := r.db.Where("ipo_id = ?", ipoID).
		Order("fetched_at DESC").
		Limit(limit).
		Find(&rows).Error; err != nil {

		return nil, err

	}

	return rows, nil

}



func (r *IPORepository) UpsertFromUpstoxDetails(d *upstox.IPODetails) (bool, error) {
	var existing IPO

	err := r.db.Where("external_id = ?", d.ID).First(&existing).Error

	now := time.Now()
	created := false

	row := IPO{
		ExternalID:             d.ID,
		Symbol:                 d.Symbol,
		Name:                   d.Name,
		ISIN:                   d.ISIN,
		IssueType:              d.IssueType,
		Industry:               d.Industry,
		IssueSize:              d.IssueSize,
		PriceMin:               d.MinimumPrice,
		PriceMax:               d.MaximumPrice,
		FaceValue:              upstox.F64(d.FaceValue),
		TickSize:               upstox.F64(d.TickSize),
		LotSize:                upstox.I(d.LotSize),
		MinimumQuantity:        upstox.I(d.MinimumQuantity),
		CutoffPrice:            upstox.F64(d.CutOffPrice),
		ListingPrice:           d.ListingPrice,
		ListingExchange:        upstox.S(d.ListingExchange),
		Status:                 d.Status,
		BiddingStart:           upstox.ParseDate(d.BiddingStartDate),
		BiddingEnd:             upstox.ParseDate(d.BiddingEndDate),
		PreApplyStart:          upstox.ParseDate(upstox.S(d.Timeline.PreApplyStartDate)),
		AllotmentStart:         upstox.ParseDate(upstox.S(d.Timeline.AllotmentStartDate)),
		AllotmentDate:          upstox.ParseDate(upstox.S(d.Timeline.AllotmentDate)),
		RefundInitiation:       upstox.ParseDate(upstox.S(d.Timeline.RefundInitiationDate)),
		ListingDate:            upstox.ParseDate(upstox.S(d.Timeline.ListingDate)),
		MandateEnd:             upstox.ParseDate(upstox.S(d.Timeline.MandateEndDate)),
		DailyStartTime:         d.DailyStartTime,
		DailyEndTime:           d.DailyEndTime,
		Registrar:              upstox.S(d.RegistrarInfo.Registrar),
		RegistrarName:          upstox.S(d.RegistrarInfo.Name),
		RegistrarEmail:         upstox.S(d.RegistrarInfo.Email),
		RegistrarContactName:   upstox.S(d.RegistrarInfo.ContactName),
		RegistrarContactNumber: upstox.S(d.RegistrarInfo.ContactNumber),
		RegistrarWebsite:       upstox.S(d.RegistrarInfo.Website),
		RHPUrl:                 upstox.S(d.RHPUrl),
		DRHPUrl:                upstox.S(d.DRHPUrl),
		Subscription:           upstox.S(d.TotalSubscription),
		UpdatedAt:              now,
	}

	if errors.Is(err, gorm.ErrRecordNotFound) {
		row.CreatedAt = now

		if err := r.db.Create(&row).Error; err != nil {
			return false, err
		}

		created = true
	} else if err != nil {
		return false, err
	} else {
		// Update only fields from Upstox to avoid overwriting independently-managed fields
		updates := map[string]interface{}{
			"symbol":                  d.Symbol,
			"name":                    d.Name,
			"status":                  d.Status,
			"price_min":               d.MinimumPrice,
			"price_max":               d.MaximumPrice,
			"issue_size":              d.IssueSize,
			"industry":                d.Industry,
			"face_value":              upstox.F64(d.FaceValue),
			"tick_size":               upstox.F64(d.TickSize),
			"lot_size":                upstox.I(d.LotSize),
			"minimum_quantity":        upstox.I(d.MinimumQuantity),
			"cutoff_price":            upstox.F64(d.CutOffPrice),
			"listing_price":           d.ListingPrice,
			"listing_exchange":        upstox.S(d.ListingExchange),
			"bidding_start":           upstox.ParseDate(d.BiddingStartDate),
			"bidding_end":             upstox.ParseDate(d.BiddingEndDate),
			"pre_apply_start":         upstox.ParseDate(upstox.S(d.Timeline.PreApplyStartDate)),
			"allotment_start":         upstox.ParseDate(upstox.S(d.Timeline.AllotmentStartDate)),
			"allotment_date":          upstox.ParseDate(upstox.S(d.Timeline.AllotmentDate)),
			"refund_initiation":       upstox.ParseDate(upstox.S(d.Timeline.RefundInitiationDate)),
			"listing_date":            upstox.ParseDate(upstox.S(d.Timeline.ListingDate)),
			"mandate_end":             upstox.ParseDate(upstox.S(d.Timeline.MandateEndDate)),
			"daily_start_time":        d.DailyStartTime,
			"daily_end_time":          d.DailyEndTime,
			"registrar":               upstox.S(d.RegistrarInfo.Registrar),
			"registrar_name":          upstox.S(d.RegistrarInfo.Name),
			"registrar_email":         upstox.S(d.RegistrarInfo.Email),
			"registrar_contact_name":  upstox.S(d.RegistrarInfo.ContactName),
			"registrar_contact_number": upstox.S(d.RegistrarInfo.ContactNumber),
			"registrar_website":       upstox.S(d.RegistrarInfo.Website),
			"rhp_url":                 upstox.S(d.RHPUrl),
			"drhp_url":                upstox.S(d.DRHPUrl),
			"subscription":            upstox.S(d.TotalSubscription),
			"updated_at":              now,
		}

		if err := r.db.Model(&existing).Updates(updates).Error; err != nil {
			return false, err
		}
	}

	return created, nil
}

