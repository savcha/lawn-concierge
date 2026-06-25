variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "us-central1"
}

variable "container_image" {
  description = "Full container image path (e.g., us-central1-docker.pkg.dev/PROJECT/lawn-concierge/app:latest)"
  type        = string
}
