data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.instance_type
  subnet_id                   = aws_subnet.public_a.id
  vpc_security_group_ids      = [aws_security_group.ec2_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_profile.name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              dnf update -y
              dnf install -y docker git
              systemctl enable --now docker
              if [ -n "${var.repo_url}" ]; then
                git clone ${var.repo_url} /opt/ticketdesk
                cd /opt/ticketdesk/app
                docker build -t ticketdesk:latest .
                docker run -d --restart always -p 8000:8000 \
                  -e AWS_REGION=${var.aws_region} \
                  -e AWS_SECRET_NAME=${aws_secretsmanager_secret.db_creds.name} \
                  -e S3_BUCKET_NAME=${aws_s3_bucket.attachments.bucket} \
                  ticketdesk:latest
              fi
              EOF

  tags = { Name = "${var.project_name}-ec2" }
}
