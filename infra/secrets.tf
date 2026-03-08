# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------

resource "aws_secretsmanager_secret" "spotify" {
  name = "terminalify/spotify-credentials"

  tags = {
    Name = "terminalify-spotify-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "spotify" {
  secret_id = aws_secretsmanager_secret.spotify.id
  secret_string = jsonencode({
    client_id     = var.spotify_client_id
    client_secret = var.spotify_client_secret
  })
}
