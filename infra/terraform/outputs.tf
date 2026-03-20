output "ec2_public_ip" {
  description = "IP público fixo da EC2 (Elastic IP)"
  value       = aws_eip.api.public_ip
}

output "ec2_public_dns" {
  description = "DNS público da EC2"
  value       = aws_instance.api.public_dns
}

output "ecr_repository_url" {
  description = "URL do repositório ECR para push de imagens"
  value       = aws_ecr_repository.api.repository_url
}

output "api_url" {
  description = "URL da API"
  value       = "http://${aws_eip.api.public_ip}:8000"
}

output "ssh_command" {
  description = "Comando SSH para acessar a instância"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ec2-user@${aws_eip.api.public_ip}"
}
