locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    },
    var.tags
  )

  github_oidc_provider_arn = (
    var.create_github_oidc_provider
    ? aws_iam_openid_connect_provider.github[0].arn
    : var.github_oidc_provider_arn
  )

  lambda_environment = merge(
    {
      DJANGO_ENV                        = "production"
      DEBUG                             = "False"
      SECRET_KEY                        = aws_ssm_parameter.django_secret_key.value
      ALLOWED_HOSTS                     = var.allowed_hosts
      CORS_ALLOWED_ORIGINS              = var.cors_allowed_origins
      DATABASE_URL                      = aws_ssm_parameter.database_url.value
      JWT_ACCESS_TOKEN_LIFETIME_MINUTES = tostring(var.jwt_access_token_lifetime_minutes)
      JWT_REFRESH_TOKEN_LIFETIME_DAYS   = tostring(var.jwt_refresh_token_lifetime_days)
      AWS__USE_S3                       = "False"
      AWS__REGION                       = var.aws_region
      API_GATEWAY_BASE_PATH             = "/${var.api_stage_name}"
      SERVE_STATIC_FILES                = "True"
      PYTHONPATH                        = "/var/task"
    },
    var.extra_lambda_env
  )
}
