resource "aws_dynamodb_table" "auth_sessions" {
  name         = "terminalify-auth-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name = "terminalify-auth-sessions"
  }
}
