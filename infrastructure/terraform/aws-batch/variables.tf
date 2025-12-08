variable "region" {
  type        = string
  description = "AWS region"
  default     = "eu-west-2"
}

variable "bucket" {
  type        = string
  description = "S3 bucket name"
  default     = "kestra-advent"
}