# Project TicketDesk - AWS POC

## 1. Local Setup & Automated Tests (M0 / M1)
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r app/requirements.txt
pytest -v
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Open `http://localhost:8000` (Login: `admin` / `admin123`).

## 2. Docker Build & Run
```bash
docker build -t ticketdesk:latest ./app
docker run -p 8000:8000 ticketdesk:latest
```

## 3. AWS Deployment via Terraform (M2 / M3 / M4)
```bash
cd terraform
terraform init
export TF_VAR_db_password="StrongPassword123!"
export TF_VAR_repo_url="https://github.com/YOUR_USERNAME/ticketdesk-aws-poc.git"
terraform apply -auto-approve
```

## 4. Teardown & Cleanup Evidence (Pass/Fail Rule #5)
```bash
cd terraform
terraform destroy -auto-approve
```
