project       = "equilibrium"
aws_region    = "us-east-1"
instance_type = "t3.small"

# Nome do Key Pair criado na AWS (sem extensão .pem)
key_pair_name = "equilibrium-key"

# Restrinja para o seu IP: "SEU_IP/32"
allowed_ssh_cidr = "0.0.0.0/0"
