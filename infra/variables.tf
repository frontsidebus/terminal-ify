variable "aws_region" {
  description = "AWS region for all resources. Must be us-east-1 for ACM certificates used with API Gateway."
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Custom domain name for the API Gateway."
  type        = string
  default     = "terminalify.343-guilty-spark.io"
}

variable "spotify_client_id" {
  description = "Spotify OAuth application client ID."
  type        = string
  sensitive   = true
}

variable "spotify_client_secret" {
  description = "Spotify OAuth application client secret."
  type        = string
  sensitive   = true
}
