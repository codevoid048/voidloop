resource "aws_cloudwatch_log_group" "backend_lambda" {
  name              = "/aws/lambda/${local.name_prefix}"
  retention_in_days = var.log_retention_days
}

resource "aws_lambda_function" "backend" {
  function_name = local.name_prefix
  role          = aws_iam_role.backend_lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.backend.repository_url}:${var.lambda_image_tag}"

  architectures = [var.lambda_architecture]
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout
  publish       = true

  ephemeral_storage {
    size = var.lambda_ephemeral_storage_mb
  }

  environment {
    variables = local.lambda_environment
  }

  tracing_config {
    mode = "Active"
  }

  # CI / build.sh update the image via update-function-code; keep TF from reverting.
  lifecycle {
    ignore_changes = [image_uri]
  }

  depends_on = [
    aws_cloudwatch_log_group.backend_lambda,
    aws_ecr_repository_policy.backend,
  ]
}
