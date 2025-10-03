# Terraform Outputs - Information needed after deployment

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP region"
  value       = var.region
}

output "zone" {
  description = "GCP zone"
  value       = var.zone
}

output "cluster_name" {
  description = "GKE cluster name"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE cluster endpoint"
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "GKE cluster CA certificate"
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "db_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "db_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "db_private_ip" {
  description = "Cloud SQL private IP address"
  value       = google_sql_database_instance.postgres.private_ip_address
}

output "db_name" {
  description = "Database name"
  value       = google_sql_database.database.name
}

output "db_user" {
  description = "Database user"
  value       = google_sql_user.user.name
}

output "db_password" {
  description = "Database password (sensitive)"
  value       = google_sql_user.user.password
  sensitive   = true
}

output "kubectl_connection_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --zone=${var.zone} --project=${var.project_id}"
}

output "next_steps" {
  description = "Next steps after deployment"
  value = <<-EOT
  
  🎉 Infrastructure deployed successfully!
  
  Next steps:
  
  1. Configure kubectl to connect to your cluster:
     ${format("gcloud container clusters get-credentials %s --zone=%s --project=%s", google_container_cluster.primary.name, var.zone, var.project_id)}
  
  2. Verify cluster access:
     kubectl get nodes
  
  3. Deploy your application:
     kubectl apply -f ../k8s/namespace.yml
     kubectl apply -f ../k8s/postgres/
     kubectl apply -f ../k8s/flask-app/
     kubectl apply -f ../k8s/nginx/
     kubectl apply -f ../k8s/monitoring/
  
  4. Get the Load Balancer IP:
     kubectl get service nginx-service -n budget-app
     (Wait a few minutes for external IP to be assigned)
  
  5. Access your app:
     http://<EXTERNAL-IP>
  
  Database connection details (for K8s secrets):
     Host: ${google_sql_database_instance.postgres.private_ip_address}
     Database: ${google_sql_database.database.name}
     User: ${google_sql_user.user.name}
     Password: (stored in Terraform state - run: terraform output db_password)
  
  EOT
}


