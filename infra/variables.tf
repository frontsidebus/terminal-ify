variable "aws_region" {
  description = "AWS region for all resources. Must be us-east-1 for ACM certificates used with API Gateway."
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "Must be a valid AWS region identifier (e.g. us-east-1)."
  }
}

variable "domain_name" {
  description = "Custom domain name for the API Gateway."
  type        = string
  default     = "terminalify.343-guilty-spark.io"

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]+[a-z0-9]$", var.domain_name))
    error_message = "Must be a valid domain name."
  }
}

variable "spotify_client_id" {
  description = "Spotify OAuth application client ID."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.spotify_client_id) > 0
    error_message = "Spotify client ID must not be empty."
  }
}

variable "spotify_client_secret" {
  description = "Spotify OAuth application client secret."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.spotify_client_secret) > 0
    error_message = "Spotify client secret must not be empty."
  }
}

variable "lambda_log_retention_days" {
  description = "Number of days to retain Lambda CloudWatch logs."
  type        = number
  default     = 14

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365], var.lambda_log_retention_days)
    error_message = "Must be a valid CloudWatch log retention value."
  }
}

variable "api_throttling_burst_limit" {
  description = "API Gateway default route throttling burst limit."
  type        = number
  default     = 50
}

variable "api_throttling_rate_limit" {
  description = "API Gateway default route throttling rate limit (requests per second)."
  type        = number
  default     = 100
}
