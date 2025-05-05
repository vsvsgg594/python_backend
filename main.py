from fastapi import FastAPI, Request
from database import engine, get_db, db_dependency
import models
import asyncio
import websockets
import time
from fastapi.middleware.cors import CORSMiddleware
from routes import customerSettings, user, chat, authentication, product, ordercoupons, admin, helpers, discount, banner, order, productreview, loyality, services, map, cart, favourites, feedback, tax, verifyredis, incentive, slottime, deliveryAgent, payment,deliveryagentpersonaldata,getuserloc,delivaryagentorder,usersearch,appfeedback,giftcard,merchant,merchantproductreview,cancellation,terminology,managecities, geofencing,preference,deliverysettings,commission,cancellationpolicy, referral,manager

import pytz
from apscheduler.triggers.date import DateTrigger
from contextlib import asynccontextmanager
from routes.helpers import populate_initial_data, merchantCancellation
from routes.scheduler import scheduler
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime


# Initialize the scheduler
#scheduler = AsyncIOScheduler()

# Main function to start the scheduler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    scheduler.start()

    # Access the database session using get_db
    db = next(get_db())
    load_tasks_from_db(db)
    populate_initial_data(db)

    yield  # Here, the application runs

    # Shutdown actions
    scheduler.shutdown()

# python -m venv env
# source env/bin/activate
#  PowerShell -ExecutionPolicy Bypass 
# myenv/scripts/Activate


app = FastAPI(lifespan=lifespan,
                # docs_url=None,
                title="Orado Order At Door",
                description="Food Delivery Application",
                    
                version="1.0.0",)

# lifespan=lifespan,
#                 docs_url=None,
#                 title="Orado: Order At Door",
#                 description="Food Delivery Application",
                
                    
#                 version="1.0.0",
                
            

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["OPTIONS", "GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)
app.add_middleware(SessionMiddleware, secret_key="0023nnamaijjirejn390**#$NFK#(DMMM)")

@app.middleware("http")
async def log_ip_and_api(request: Request, call_next):
    client_ip = request.client.host  # Get client IP
    api_name = request.url.path      # Get API path
    method = request.method          # Get HTTP method
    log_entry = f"{datetime.now()} - IP: {client_ip}, API: {method} {api_name}\n"
    
    # Save log to a file (or database if needed)
    with open("api_logs.txt", "a") as log_file:
        log_file.write(log_entry)
    
    # Process the request
    response = await call_next(request)
    return response

app.include_router(admin.router)
app.include_router(authentication.router)
app.include_router(banner.router)
app.include_router(cart.router)
app.include_router(chat.router)
app.include_router(deliveryAgent.router)
app.include_router(discount.router)
app.include_router(favourites.router)
app.include_router(feedback.router)
app.include_router(helpers.router)
app.include_router(incentive.router)
app.include_router(loyality.router)
app.include_router(map.router)
app.include_router(order.router)
app.include_router(ordercoupons.router)
app.include_router(payment.router)
app.include_router(product.router)
app.include_router(productreview.router)
app.include_router(services.router)
app.include_router(slottime.router)
app.include_router(tax.router)
app.include_router(user.router)
app.include_router(deliveryagentpersonaldata.router) 
app.include_router(getuserloc.router) 
app.include_router(delivaryagentorder.router) 
app.include_router(usersearch.router)
app.include_router(appfeedback.router)
app.include_router(giftcard.router)
app.include_router(merchant.router)
app.include_router(merchantproductreview.router)
app.include_router(cancellation.router)
app.include_router(terminology.router)
app.include_router(managecities.router)
app.include_router(preference.router)
app.include_router(geofencing.router)
app.include_router(deliverysettings.router)
app.include_router(commission.router)
app.include_router(cancellationpolicy.router)
app.include_router(referral.router)
app.include_router(customerSettings.router)
app.include_router(manager.router)


# models.Base.metadata.create_all(bind=engine)


"""@app.post("/merchant/")
def merchant(shopname:str,)"""


@app.get("/health-check")
async def gethello():
    return "system is fine"

# async def test_latency(uri):
#     try:
#         async with websockets.connect(uri) as websocket:
#             message = "ping"
#             start_time = time.time()
#             await websocket.send(message)
#             response = await websocket.recv()
#             end_time = time.time()
#             latency = (end_time - start_time) * 1000  # Convert to milliseconds
#             if response == message:
#                 print(f"Round-trip latency: {latency:.2f} ms")
#             else:
#                 print(f"Unexpected response: {response}")
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     uri = "ws://localhost:8000/ws"  # Update with your WebSocket URL
#     asyncio.run(test_latency(uri))

def load_tasks_from_db(db: db_dependency):
    schedules = db.query(models.setSchedule).filter(models.setSchedule.executionStatus == 1).all()
    for myschedule in schedules:
        sgt_timestamp = myschedule.timeStamp.astimezone(pytz.timezone('Asia/Singapore'))
        trigger = DateTrigger(run_date=sgt_timestamp)
        scheduler.add_job(
            merchantCancellation,
            trigger,
            args=[myschedule.jobId, db],
            id=str(myschedule.jobId),
            replace_existing=True
        )

#print(str(products.statement.compile(compile_kwargs={"literal_binds": True})))
