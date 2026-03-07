resource "aws_acm_certificate" "api" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  tags = {
    Name = "terminalify-api-cert"
  }

  lifecycle {
    create_before_destroy = true
  }
}
