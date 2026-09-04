package upstox

import "time"

type GetIPOsResponse struct {
	Status string `json:"status"`

	Data []IPOSummary `json:"data"`

	MetaData struct {
		Page struct {
			PageNumber int `json:"page_number"`

			TotalPages int `json:"total_pages"`

			Records int `json:"records"`

			TotalRecords int `json:"total_records"`
		} `json:"page"`
	} `json:"meta_data"`
}

type IPOSummary struct {
	ID string `json:"id"`

	Symbol string `json:"symbol"`

	Name string `json:"name"`

	Status string `json:"status"`

	ISIN string `json:"isin"`

	IssueType string `json:"issue_type"`

	IssueSize float64 `json:"issue_size"`

	Industry string `json:"industry"`

	MinimumPrice float64 `json:"minimum_price"`

	MaximumPrice float64 `json:"maximum_price"`

	BiddingStartDate string `json:"bidding_start_date"`

	BiddingEndDate string `json:"bidding_end_date"`

	TotalSubscription string `json:"total_subscription"`
}

type GetIPODetailsResponse struct {
	Status string `json:"status"`

	Data IPODetails `json:"data"`
}

type IPODetails struct {
	ID string `json:"id"`

	Symbol string `json:"symbol"`

	Name string `json:"name"`

	Status string `json:"status"`

	ISIN string `json:"isin"`

	IssueType string `json:"issue_type"`

	IssueSize float64 `json:"issue_size"`

	Industry string `json:"industry"`

	MinimumPrice float64 `json:"minimum_price"`

	MaximumPrice float64 `json:"maximum_price"`

	BiddingStartDate string `json:"bidding_start_date"`

	BiddingEndDate string `json:"bidding_end_date"`

	DailyStartTime string `json:"daily_start_time"`

	DailyEndTime string `json:"daily_end_time"`

	FaceValue *float64 `json:"face_value"`

	TickSize *float64 `json:"tick_size"`

	LotSize *int `json:"lot_size"`

	MinimumQuantity *int `json:"minimum_quantity"`

	CutOffPrice *float64 `json:"cut_off_price"`

	ListingPrice *float64 `json:"listing_price"`

	ListingExchange *string `json:"listing_exchange"`

	RHPUrl *string `json:"rhp_url"`

	DRHPUrl *string `json:"drhp_url"`

	Timeline Timeline `json:"timeline"`

	RegistrarInfo RegistrarInfo `json:"registrar_info"`

	TotalSubscription *string `json:"total_subscription"`
}

type Timeline struct {
	PreApplyStartDate *string `json:"pre_apply_start_date"`

	ApplicationStartDate *string `json:"application_start_date"`

	ApplicationEndDate *string `json:"application_end_date"`

	AllotmentStartDate *string `json:"allotment_start_date"`

	AllotmentDate *string `json:"allotment_date"`

	RefundInitiationDate *string `json:"refund_initiation_date"`

	ListingDate *string `json:"listing_date"`

	MandateEndDate *string `json:"mandate_end_date"`
}

type RegistrarInfo struct {
	Name *string `json:"name"`

	Email *string `json:"email"`

	ContactName *string `json:"contact_name"`

	ContactNumber *string `json:"contact_number"`

	Website *string `json:"website"`

	Registrar *string `json:"registrar"`
}

func ParseDate(s string) *time.Time {

	if s == "" {

		return nil

	}

	t, err := time.Parse("2006-01-02", s)

	if err != nil {

		return nil

	}

	return &t

}

func F64(p *float64) float64 {

	if p == nil {

		return 0

	}

	return *p

}

func I(p *int) int {

	if p == nil {

		return 0

	}

	return *p

}

func S(p *string) string {

	if p == nil {

		return ""

	}

	return *p

}
