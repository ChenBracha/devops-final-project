# Cloud SQL PostgreSQL Database Configuration

# Random password for database (will be stored in Terraform state)
resource "random_password" "db_password" {
  length  = 16
  special = false # Avoid special chars that might cause issues
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "postgres" {
  name             = var.db_instance_name
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro" # Smallest instance for cost savings
    availability_type = "ZONAL"       # Single zone for cost savings
    disk_size         = 10            # Minimum disk size (GB)
    disk_type         = "PD_SSD"

    backup_configuration {
      enabled            = true
      start_time         = "02:00"
      point_in_time_recovery_enabled = false # Disable for cost savings
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.vpc.id
      
      # Allow GKE to connect
      require_ssl = false # Set to true in production!
    }

    maintenance_window {
      day  = 7 # Sunday
      hour = 3
    }
  }

  deletion_protection = false # Allow deletion via Terraform (set to true in production!)

  depends_on = [
    google_project_service.sqladmin,
    google_service_networking_connection.private_vpc_connection
  ]
}

# Create database
resource "google_sql_database" "database" {
  name     = var.db_name
  instance = google_sql_database_instance.postgres.name
}

# Create database user
resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.postgres.name
  password = var.db_password != "" ? var.db_password : random_password.db_password.result
}

# Private VPC connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${var.cluster_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}


