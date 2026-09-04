package models

import (
	"errors"

	"gorm.io/gorm"
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
