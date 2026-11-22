import os
import json
import logging
import boto3
from fastapi import FastAPI, Form, File, UploadFile, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ticketdesk")

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
SECRET_NAME = os.getenv("AWS_SECRET_NAME", "")

def load_db_url():
    if SECRET_NAME:
        try:
            sm = boto3.client("secretsmanager", region_name=AWS_REGION)
            secret = json.loads(sm.get_secret_value(SecretId=SECRET_NAME)["SecretString"])
            return f"postgresql://{secret['username']}:{secret['password']}@{secret['host']}:{secret.get('port', 5432)}/{secret['dbname']}"
        except Exception as e:
            logger.error(f"Failed to fetch secret {SECRET_NAME}: {e}")
    return os.getenv("DATABASE_URL", "sqlite:///./ticketdesk.db")

DATABASE_URL = load_db_url()
S3_BUCKET = os.getenv("S3_BUCKET_NAME", "")
APP_USER = os.getenv("APP_USER", "admin")
APP_PASS = os.getenv("APP_PASS", "admin123")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=False)
    status = Column(String(50), default="Open")
    attachment = Column(String(500), nullable=True)

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Project TicketDesk")

os.makedirs("uploads", exist_ok=True)
s3_client = boto3.client("s3", region_name=AWS_REGION) if S3_BUCKET else None

def is_logged_in(user: str | None):
    return user == APP_USER

@app.get("/health")
def health_check():
    return JSONResponse({"status": "healthy", "service": "ticketdesk", "s3_enabled": bool(S3_BUCKET)})

@app.get("/", response_class=HTMLResponse)
def home(user: str | None = Cookie(default=None)):
    if not is_logged_in(user):
        return RedirectResponse("/login", status_code=302)
    db = SessionLocal()
    tickets = db.query(Ticket).order_by(Ticket.id.desc()).all()
    db.close()

    counts = {s: sum(1 for t in tickets if t.status == s) for s in ["Open", "In Progress", "Resolved", "Closed"]}
    rows = ""
    for t in tickets:
        att = t.attachment or "None"
        rows += f"""
        <tr>
            <td>#{t.id}</td>
            <td><b>{t.title}</b><br><small>{t.description}</small></td>
            <td>{t.status}</td>
            <td>{att}</td>
            <td>
                <form method="post" action="/tickets/{t.id}/status" style="margin:0;">
                    <select name="status">
                        {''.join(f'<option value="{s}" {"selected" if t.status==s else ""}>{s}</option>' for s in ["Open", "In Progress", "Resolved", "Closed"])}
                    </select>
                    <button type="submit">Update</button>
                </form>
            </td>
        </tr>"""

    return f"""
    <html><head><title>TicketDesk</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 960px; margin: 30px auto; padding: 0 15px; }}
        .cards {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .card {{ flex: 1; padding: 15px; background: #f4f6f8; border-radius: 6px; text-align: center; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #222; color: #fff; }}
    </style></head>
    <body>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <h1>Project TicketDesk</h1>
            <a href="/logout">Logout ({user})</a>
        </div>
        <div class="cards">
            <div class="card"><h3>Open</h3><h2>{counts['Open']}</h2></div>
            <div class="card"><h3>In Progress</h3><h2>{counts['In Progress']}</h2></div>
            <div class="card"><h3>Resolved</h3><h2>{counts['Resolved']}</h2></div>
            <div class="card"><h3>Closed</h3><h2>{counts['Closed']}</h2></div>
        </div>
        <h3>Create Support Ticket</h3>
        <form method="post" action="/tickets" enctype="multipart/form-data">
            <input name="title" placeholder="Ticket Title" required style="width:30%; padding:8px;">
            <input name="description" placeholder="Issue Description" required style="width:40%; padding:8px;">
            <input type="file" name="file">
            <button type="submit" style="padding:8px 16px;">Create</button>
        </form>
        <table>
            <tr><th>ID</th><th>Ticket</th><th>Status</th><th>Attachment</th><th>Action</th></tr>
            {rows or '<tr><td colspan="5">No tickets yet.</td></tr>'}
        </table>
    </body></html>
    """

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
    <html><body style="font-family:Arial; max-width:350px; margin:80px auto;">
        <h2>TicketDesk Login</h2>
        <form method="post" action="/login">
            <input name="username" placeholder="Username" required style="width:100%; padding:8px; margin-bottom:10px;"><br>
            <input name="password" type="password" placeholder="Password" required style="width:100%; padding:8px; margin-bottom:10px;"><br>
            <button type="submit" style="width:100%; padding:10px;">Login</button>
        </form>
    </body></html>
    """

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    if username == APP_USER and password == APP_PASS:
        logger.info(f"User {username} logged in")
        resp = RedirectResponse("/", status_code=302)
        resp.set_cookie(key="user", value=username, httponly=True)
        return resp
    return HTMLResponse("Invalid credentials. <a href='/login'>Try again</a>", status_code=401)

@app.get("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("user")
    return resp

@app.post("/tickets")
async def create_ticket(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile | None = File(default=None),
    user: str | None = Cookie(default=None)
):
    if not is_logged_in(user):
        return RedirectResponse("/login", status_code=302)

    attachment_ref = None
    if file and file.filename:
        content = await file.read()
        if s3_client and S3_BUCKET:
            s3_client.put_object(Bucket=S3_BUCKET, Key=f"attachments/{file.filename}", Body=content)
            attachment_ref = f"s3://{S3_BUCKET}/attachments/{file.filename}"
            logger.info(f"Uploaded attachment to {attachment_ref}")
        else:
            path = os.path.join("uploads", file.filename)
            with open(path, "wb") as f:
                f.write(content)
            attachment_ref = f"local:{file.filename}"

    db = SessionLocal()
    ticket = Ticket(title=title, description=description, status="Open", attachment=attachment_ref)
    db.add(ticket)
    db.commit()
    logger.info(f"Created ticket #{ticket.id}: {title}")
    db.close()
    return RedirectResponse("/", status_code=302)

@app.post("/tickets/{ticket_id}/status")
def update_status(ticket_id: int, status: str = Form(...), user: str | None = Cookie(default=None)):
    if not is_logged_in(user):
        return RedirectResponse("/login", status_code=302)
    db = SessionLocal()
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        ticket.status = status
        db.commit()
        logger.info(f"Updated ticket #{ticket_id} status to {status}")
    db.close()
    return RedirectResponse("/", status_code=302)
