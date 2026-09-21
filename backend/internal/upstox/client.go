package upstox

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"

	"net/http"

	"net/url"

	"time"
)

const baseURL = "https://api.upstox.com/v2"

type Client struct {
	token string

	http *http.Client
}

func NewClient(token string) *Client {

	return &Client{token: token, http: &http.Client{Timeout: 30 * time.Second}}

}

func (c *Client) GetIPOs(status, issueType string, page, records int) (*GetIPOsResponse, error) {
	// Validate token before making request
	if c.token == "" || strings.TrimSpace(c.token) == "" {
		return nil, fmt.Errorf("invalid token: token is empty or whitespace")
	}

	if status == "" {
		status = "open"
	}

	if records <= 0 || records > 30 {
		records = 30
	}

	if page < 1 {
		page = 1
	}

	q := url.Values{}
	q.Set("status", status)
	if issueType != "" {
		q.Set("issue_type", issueType)
	}
	q.Set("page_number", fmt.Sprintf("%d", page))
	q.Set("records", fmt.Sprintf("%d", records))

	endpoint := fmt.Sprintf("%s/ipos?%s", baseURL, q.Encode())

	req, err := http.NewRequest(http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}

	req.Header.Set("Accept", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.token)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("upstox call failed: %w", err)
	}

	defer resp.Body.Close()

	// Handle rate limiting with retry suggestion
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, fmt.Errorf("upstox rate limit exceeded (HTTP 429)")
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
		return nil, fmt.Errorf("upstox status %d for %s: %s", resp.StatusCode, endpoint, strings.TrimSpace(string(body)))
	}

	var out GetIPOsResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	if out.Status != "success" {
		return nil, fmt.Errorf("upstox non-success status: %s", out.Status)
	}

	return &out, nil
}

func (c *Client) GetIPODetails(id string) (*GetIPODetailsResponse, error) {
	// Validate token before making request
	if c.token == "" || strings.TrimSpace(c.token) == "" {
		return nil, fmt.Errorf("invalid token: token is empty or whitespace")
	}

	endpoint := fmt.Sprintf("%s/ipos/%s", baseURL, id)

	req, err := http.NewRequest(http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("build request: %w", err)
	}

	req.Header.Set("Accept", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.token)

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("upstox call failed: %w", err)
	}

	defer resp.Body.Close()

	// Handle rate limiting
	if resp.StatusCode == http.StatusTooManyRequests {
		return nil, fmt.Errorf("upstox rate limit exceeded (HTTP 429)")
	}

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("upstox status %d for %s", resp.StatusCode, endpoint)
	}

	var out GetIPODetailsResponse
	if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}

	if out.Status != "success" {
		return nil, fmt.Errorf("upstox non-success status: %s", out.Status)
	}

	return &out, nil
}
