# ─── IAM: permite EC2 fazer pull no ECR ──────────────────────────────────────

resource "aws_iam_role" "ec2" {
  name = "${var.project}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_ecr" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project}-ec2-profile"
  role = aws_iam_role.ec2.name
}

# ─── Security Group ───────────────────────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "${var.project}-ec2-sg"
  description = "EC2 - API exposta na 8000, SSH restrito"

  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-ec2-sg" }
}

# ─── AMI: Amazon Linux 2023 (mais recente) ───────────────────────────────────

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# ─── EC2 Instance ─────────────────────────────────────────────────────────────

resource "aws_instance" "api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_pair_name
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  vpc_security_group_ids = [aws_security_group.ec2.id]

  root_block_device {
    volume_size = 40
    volume_type = "gp3"
  }

  # Instala Docker e autentica no ECR na inicialização
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Instalar Docker
    dnf install -y docker
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user

    # Instalar Docker Compose v2
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # Autenticar no ECR via IAM role (sem credenciais hardcoded)
    AWS_REGION="${var.aws_region}"
    ECR_REGISTRY="${aws_ecr_repository.api.registry_id}.dkr.ecr.${var.aws_region}.amazonaws.com"

    # Adicionar helper de credenciais do ECR
    dnf install -y amazon-ecr-credential-helper
    mkdir -p /home/ec2-user/.docker
    cat > /home/ec2-user/.docker/config.json <<DOCKER
    {
      "credHelpers": {
        "$ECR_REGISTRY": "ecr-login"
      }
    }
    DOCKER
    chown -R ec2-user:ec2-user /home/ec2-user/.docker

    # Diretório da aplicação
    mkdir -p /opt/app
    chown ec2-user:ec2-user /opt/app
  EOF

  tags = { Name = "${var.project}-api" }
}

# ─── Elastic IP (IP fixo para DNS/SSH) ───────────────────────────────────────

resource "aws_eip" "api" {
  instance = aws_instance.api.id
  domain   = "vpc"

  tags = { Name = "${var.project}-api-eip" }
}
