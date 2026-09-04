package models

import (
	"time"

	"gorm.io/gorm"
)

type IPO struct {
	ID uint `gorm:"primaryKey" json:"id"`

	ExternalID string `gorm:"uniqueIndex;not null" json:"external_id"`

	Symbol string `json:"symbol"`

	Name string `gorm:"not null;index" json:"name"`

	ISIN string `gorm:"index" json:"isin"`

	IssueType string `json:"issue_type"`

	Industry string `json:"industry"`

	IssueSize float64 `json:"issue_size"`

	PriceMin float64 `json:"price_min"`

	PriceMax float64 `json:"price_max"`

	FaceValue float64 `json:"face_value"`

	TickSize float64 `json:"tick_size"`

	LotSize int `json:"lot_size"`

	MinimumQuantity int `json:"minimum_quantity"`

	CutoffPrice float64 `json:"cutoff_price"`

	ListingPrice *float64 `json:"listing_price,omitempty"`

	ListingExchange string `json:"listing_exchange"`

	Status string `gorm:"index" json:"status"`

	BiddingStart *time.Time `json:"bidding_start,omitempty"`

	BiddingEnd *time.Time `json:"bidding_end,omitempty"`

	PreApplyStart *time.Time `json:"pre_apply_start,omitempty"`

	AllotmentStart *time.Time `json:"allotment_start,omitempty"`

	AllotmentDate *time.Time `json:"allotment_date,omitempty"`

	RefundInitiation *time.Time `json:"refund_initiation,omitempty"`

	ListingDate *time.Time `json:"listing_date,omitempty"`

	MandateEnd *time.Time `json:"mandate_end,omitempty"`

	DailyStartTime string `json:"daily_start_time,omitempty"`

	DailyEndTime string `json:"daily_end_time,omitempty"`

	Registrar string `gorm:"index" json:"registrar"`

	RegistrarName string `json:"registrar_name"`

	RegistrarEmail string `json:"registrar_email"`

	RegistrarContactName string `json:"registrar_contact_name"`

	RegistrarContactNumber string `json:"registrar_contact_number"`

	RegistrarPhone string `json:"registrar_phone"`

	RegistrarWebsite string `json:"registrar_website"`

	RHPUrl string `json:"rhp_url"`

	DRHPUrl string `json:"drhp_url"`

	Subscription string `json:"subscription"`

	CreatedAt time.Time `json:"created_at"`

	UpdatedAt time.Time `json:"updated_at"`

	DeletedAt gorm.DeletedAt `gorm:"index" json:"-"`
}

type IPOGMP struct {
	ID uint `gorm:"primaryKey" json:"id"`

	IPOID uint `gorm:"index;not null" json:"ipo_id"`

	GMPPrice *float64 `json:"gmp_price"`

	GMPPercentage *float64 `json:"gmp_percentage"`

	EstimatedListingPrice *float64 `json:"estimated_listing_price"`

	Source string `gorm:"not null" json:"source"`

	SourceUpdatedAt *time.Time `json:"source_updated_at,omitempty"`

	FetchedAt time.Time `gorm:"index" json:"fetched_at"`
}

type IPOGMPHistory struct {
	ID uint `gorm:"primaryKey" json:"id"`

	IPOID uint `gorm:"index;not null" json:"ipo_id"`

	GMPPrice *float64 `json:"gmp_price"`

	GMPPercentage *float64 `json:"gmp_percentage"`

	EstimatedListingPrice *float64 `json:"estimated_listing_price"`

	Source string `gorm:"not null" json:"source"`

	SourceUpdatedAt *time.Time `json:"source_updated_at,omitempty"`

	FetchedAt time.Time `gorm:"index" json:"fetched_at"`
}

func (IPOGMP) TableName() string { return "ipo_gmp" }

func (IPOGMPHistory) TableName() string { return "ipo_gmp_history" }

func (IPO) TableName() string { return "ipos" }
