output "api_gateway_url" {
  description = "Default API Gateway endpoint URL."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "custom_domain_target" {
  description = "API Gateway domain name to CNAME to in Namecheap."
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
}

output "certificate_validation_records" {
  description = "CNAME records to add in Namecheap for ACM certificate DNS validation."
  value = {
    for dvo in aws_acm_certificate.api.domain_validation_options : dvo.domain_name => {
      name  = dvo.resource_record_name
      type  = dvo.resource_record_type
      value = dvo.resource_record_value
    }
  }
}

output "callback_url" {
  description = "Full Spotify OAuth callback URL to register in the Spotify Developer Dashboard."
  value       = "https://${var.domain_name}/callback"
}
