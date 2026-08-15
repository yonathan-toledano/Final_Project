data "http" "my_public_ip" {
  url = "https://ipv4.icanhazip.com"
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  my_ip_cidr = "${chomp(data.http.my_public_ip.response_body)}/32"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "${var.project_name}-vpc"
  cidr = "10.40.0.0/16"

  azs                  = [data.aws_availability_zones.available.names[0]]
  public_subnets       = ["10.40.1.0/24"]
  enable_nat_gateway   = false
  single_nat_gateway   = false
  enable_dns_support   = true
  enable_dns_hostnames = true

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  tags = {
    Project     = var.project_name
    ManagedBy   = "Terraform"
    Environment = "final"
  }
}

resource "aws_security_group" "k3s" {
  name        = "${var.project_name}-sg"
  description = "Allow SSH and HTTP from my IP"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [local.my_ip_cidr]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [local.my_ip_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-sg"
  }
}

resource "aws_instance" "k3s" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  subnet_id                   = module.vpc.public_subnets[0]
  vpc_security_group_ids      = [aws_security_group.k3s.id]
  associate_public_ip_address = true
  user_data = templatefile("${path.module}/user-data.sh", {
    repository_url    = var.repository_url
    repository_branch = var.repository_branch
    app_namespace     = var.app_namespace
    argocd_namespace  = var.argocd_namespace
  })

  root_block_device {
    volume_size = 16
    volume_type = "gp3"
  }

  tags = {
    Name = var.project_name
  }

  user_data_replace_on_change = true
}
