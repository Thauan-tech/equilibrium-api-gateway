variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "equilibrium"
}

variable "instance_type" {
  type        = string
  description = "Tipo da instância EC2"
  default     = "t3.small"
}

variable "key_pair_name" {
  type        = string
  description = "Nome do Key Pair AWS para acesso SSH à EC2"
}

variable "allowed_ssh_cidr" {
  type        = string
  description = "IP autorizado para SSH (ex: seu IP público/32)"
  default     = "0.0.0.0/0"
}
