output "ec2_public_ip" {
  description = "Public IP of TicketDesk EC2 instance"
  value       = aws_instance.app.public_ip
}

output "app_url" {
  description = "TicketDesk application URL"
  value       = "http://${aws_instance.app.public_ip}:8000"
}

output "s3_bucket_name" {
  description = "S3 bucket for ticket attachments"
  value       = aws_s3_bucket.attachments.bucket
}

output "rds_endpoint" {
  description = "Private RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "lambda_function_name" {
  description = "File processor Lambda function name"
  value       = aws_lambda_function.file_processor.function_name
}
