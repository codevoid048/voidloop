resource "aws_ssm_parameter" "django_secret_key" {
  name        = "/${var.project_name}/${var.environment}/django_secret_key"
  description = "Django SECRET_KEY"
  type        = "SecureString"
  value       = var.django_secret_key
}

resource "aws_ssm_parameter" "database_url" {
  name        = "/${var.project_name}/${var.environment}/database_url"
  description = "PostgreSQL connection URL"
  type        = "SecureString"
  value       = var.database_url
}

resource "aws_ssm_parameter" "cloudflare_turnstile_secret_key" {
  name        = "/${var.project_name}/${var.environment}/cloudflare_turnstile_secret_key"
  description = "Cloudflare Turnstile secret key for auth siteverify"
  type        = "SecureString"
  value       = var.cloudflare_turnstile_secret_key
}
