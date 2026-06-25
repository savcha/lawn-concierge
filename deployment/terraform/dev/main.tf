/**
 * Lawn Concierge — Cloud Run Deployment (Dev Environment)
 *
 * Deploys the ADK agent as a Cloud Run service.
 * The container image is built from the project root using Cloud Build.
 */

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ─── Enable Required APIs ─────────────────────────────────────────────────────

resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# ─── Secrets (stored in Secret Manager for security) ─────────────────────────

resource "google_secret_manager_secret" "openweather_api_key" {
  secret_id = "lawn-concierge-openweather-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

# Note: Populate this secret after terraform apply:
# echo -n "YOUR_KEY" | gcloud secrets versions add lawn-concierge-openweather-api-key --data-file=-

# ─── Service Account ──────────────────────────────────────────────────────────

resource "google_service_account" "lawn_concierge" {
  account_id   = "lawn-concierge-sa"
  display_name = "Lawn Concierge Cloud Run Service Account"
}

resource "google_secret_manager_secret_iam_member" "sa_secret_access" {
  secret_id = google_secret_manager_secret.openweather_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.lawn_concierge.email}"
}

# Allow the service account to call Vertex AI / Gemini
resource "google_project_iam_member" "sa_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.lawn_concierge.email}"
}

# ─── Cloud Run Service ────────────────────────────────────────────────────────

resource "google_cloud_run_v2_service" "lawn_concierge" {
  name     = "lawn-concierge"
  location = var.region

  template {
    service_account = google_service_account.lawn_concierge.email

    containers {
      image = var.container_image

      # Environment variables — non-sensitive
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "AGENT_MODEL"
        value = "gemini-2.5-flash"
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }

      # Sensitive env var from Secret Manager
      env {
        name = "OPENWEATHER_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openweather_api_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }
  }

  depends_on = [
    google_project_service.run,
    google_secret_manager_secret.openweather_api_key,
  ]
}

# ─── Public Access (for demo purposes) ───────────────────────────────────────
# Remove this in production and use IAP or API Gateway instead.

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.lawn_concierge.location
  service  = google_cloud_run_v2_service.lawn_concierge.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ─── Outputs ─────────────────────────────────────────────────────────────────

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.lawn_concierge.uri
}

output "service_account_email" {
  description = "Service account email"
  value       = google_service_account.lawn_concierge.email
}
