from fastapi import FastAPI
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from app.db.db import engine, Base
from app.routers.race import race_router
from app.routers.event import event_router
from app.routers.user import router as user_router
from app.routers.notification import notification_router
from app.routers.promotions import promotion_router
from app.routers.fcm_token import fcm_token_router
from app.utils.schedular_push_notification import send_scheduled_notifications
from app.routers.notification_box import notification_box_router

from fastapi.middleware.cors import CORSMiddleware






# Load environment variables
load_dotenv()
scheduler = BackgroundScheduler()
scheduler.add_job(send_scheduled_notifications, CronTrigger(minute='*/1'))

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    if not scheduler.running:
        scheduler.start()
    yield
    scheduler.shutdown()

# FastAPI app
app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




#Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)





# Firebase initialization
firebase_cred_str = os.getenv("FIREBASE_CREDENTIALS")
if not firebase_cred_str:
    raise ValueError("❌ FIREBASE_CREDENTIALS not set in .env file!")

try:
    cred_dict = json.loads(firebase_cred_str)
    # Replace escaped newline with actual newline
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("✅ Firebase initialized successfully!")
except Exception as e:
    print("❌ Firebase initialization failed:", e)
    raise


# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Hello, FastAPI is working!"}


# Include routers
app.include_router(race_router)
app.include_router(event_router)
app.include_router(user_router)
app.include_router(notification_router)
app.include_router(promotion_router)
app.include_router(fcm_token_router)
app.include_router(notification_box_router)
