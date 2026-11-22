variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project prefix"
  type        = string
  default     = "ticketdesk"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  default     = "tdadmin"
}

variable "db_password" {
  description = "RDS master password (pass via TF_VAR_db_password, never commit)"
  type        = string
  sensitive   = true
}

variable "repo_url" {
  description = "Git repository URL containing the TicketDesk app"
  type        = string
  default     = ""
}
