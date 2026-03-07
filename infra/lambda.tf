# -----------------------------------------------------------------------------
# Lambda source package
# -----------------------------------------------------------------------------

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/callback"
  output_path = "${path.module}/build/lambda_callback.zip"
}

# -----------------------------------------------------------------------------
# IAM role and policies
# -----------------------------------------------------------------------------

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "terminalify-auth-callback-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Name = "terminalify-auth-callback-role"
  }
}

data "aws_iam_policy_document" "lambda_permissions" {
  # CloudWatch Logs
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  # DynamoDB
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:DeleteItem",
    ]
    resources = [aws_dynamodb_table.auth_sessions.arn]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "terminalify-auth-callback-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

# -----------------------------------------------------------------------------
# Lambda function
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "auth_callback" {
  function_name    = "terminalify-auth-callback"
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      SPOTIFY_CLIENT_ID     = var.spotify_client_id
      SPOTIFY_CLIENT_SECRET = var.spotify_client_secret
      DOMAIN_NAME           = var.domain_name
      DYNAMODB_TABLE        = aws_dynamodb_table.auth_sessions.name
    }
  }

  tags = {
    Name = "terminalify-auth-callback"
  }
}
