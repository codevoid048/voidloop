terraform {
  backend "s3" {
    bucket       = "voidloop-terraform-state-prod-aps2"
    key          = "prod/terraform.tfstate"
    region       = "ap-south-2"
    encrypt      = true
    use_lockfile = true
  }
}
