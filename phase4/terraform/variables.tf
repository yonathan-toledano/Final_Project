variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "finalproject-monitor"
}

variable "instance_type" {
  description = "Free Tier eligible EC2 instance type for the K3S node"
  type        = string
  default     = "t3.small"
}

variable "repository_url" {
  description = "Git repository to clone on the EC2 instance"
  type        = string
  default     = "https://github.com/yonathan-toledano/Final_Project.git"
}

variable "repository_branch" {
  description = "Branch to clone from GitHub"
  type        = string
  default     = "main"
}

variable "app_namespace" {
  description = "Kubernetes namespace for the app"
  type        = string
  default     = "monitor"
}

variable "argocd_namespace" {
  description = "ArgoCD namespace"
  type        = string
  default     = "argocd"
}
