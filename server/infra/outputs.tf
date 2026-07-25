output "ecr_repository_url" {
  description = "ECR repository URL for backend Lambda image."
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name."
  value       = aws_ecr_repository.backend.name
}

output "lambda_function_name" {
  description = "Backend Lambda function name."
  value       = aws_lambda_function.backend.function_name
}

output "api_gateway_invoke_url" {
  description = "Default API Gateway invoke URL."
  value       = aws_apigatewayv2_stage.primary.invoke_url
}

output "api_domain_name" {
  description = "Custom API domain name."
  value       = aws_apigatewayv2_domain_name.api.domain_name
}

output "api_domain_target" {
  description = "Cloudflare CNAME target for API custom domain."
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
}

output "api_domain_hosted_zone_id" {
  description = "Hosted zone ID for API custom domain target."
  value       = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
}

output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC deploy. Set as AWS_ROLE_ARN repo secret."
  value       = aws_iam_role.github_actions.arn
}
