output "instance_public_ip" {
  description = "Public IP for the K3S node"
  value       = aws_instance.k3s.public_ip
}

output "instance_public_dns" {
  description = "Public DNS for the K3S node"
  value       = aws_instance.k3s.public_dns
}

output "public_url" {
  description = "HTTP URL for the application"
  value       = "http://${aws_instance.k3s.public_ip}"
}

output "my_ip_cidr" {
  description = "Terraform-detected public IP used in the security group"
  value       = local.my_ip_cidr
}
