# Terraform Variables for GCP Deployment
# This file defines all configurable parameters

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
  default     = "budget-app-cluster"
}

variable "node_count" {
  description = "Number of nodes in the GKE cluster"
  type        = number
  default     = 2
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-small" # 2 vCPU, 2GB RAM - smallest for cost savings
}

variable "db_instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "budget-app-db"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "app"
}

variable "db_user" {
  description = "PostgreSQL database user"
  type        = string
  default     = "app"
}

variable "db_password" {
  description = "PostgreSQL database password"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"
}


