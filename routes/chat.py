import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from fastapi.responses import JSONResponse
from models import messageTable,Notification
from database import db_dependency
from routes.token import decode_token, bearer_scheme
import redis
from routes.websocketConn import connectionManager,redis_client
from typing import Optional

router = APIRouter()


# redis_client = redis.Redis(host='localhost', port=6379, db=0,decode_responses=True)


@router.get("/clear-rediscache")
async def clearRedisCache(token: Optional[str] = Depends(bearer_scheme)):
    decoded_token = decode_token(token.credentials)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    user_type = decoded_token.get('userType')
    
    if user_type != "admin":
        return JSONResponse(status_code=403, content={"detail":"You lack admin privileges"})
    
    try:
        redis_client.flushall()
        return JSONResponse(status_code=200, content={"detail": "cache cleared successfully"})
    except Exception as e:
        print(e)  
        return JSONResponse(status_code=400, content={"detail": "unable to clear cache"})

# class connectionManager:
    
#     def __init__(self):
#         self.activeconnections: Dict[str, WebSocket] = {}

#     async def connect(self, websocket: WebSocket, clientId:int):
#         await websocket.accept()
#         self.activeconnections[clientId] = websocket
        
         
    
#     def disconnect(self, client_id: int):
#         del self.activeconnections[client_id]
   
#     async def send_personal_message(self, message: str, client_id: int):
#         websocket = self.activeconnections.get(client_id)
#         if websocket:
#             await websocket.send_text(message)
    
#     async def broadcast(self, message: str, senderId: int, recieverId: int):
#         receiver_ws = self.activeconnections.get(recieverId)
#         if receiver_ws:
#             await receiver_ws.send_text(message)
#         else:
#             # If the receiver is not connected, push the message to Redis
#             redis_client.rpush(f"messages:{recieverId}", json.dumps({
#                 'sender_id': senderId,
#                 'message': message
#             }))
#         # for clientId,connection in self.activeconnections.items():
#         #     if clientId != senderId and clientId == recieverId:
#         #         await connection.send_text(message)


# manager = connectionManager()

# class ConnectionManager:
#     def __init__(self):
#         self.active_connections = {}  # Keyed by merchantId:storeId

#     async def connect(self, websocket: WebSocket, merchantId: int, storeId: int):
#         key = f"{merchantId}:{storeId}"
#         if key not in self.active_connections:
#             self.active_connections[key] = []
#         self.active_connections[key].append(websocket)
#         await websocket.accept()

#     def disconnect(self, merchantId: int, storeId: int, websocket: WebSocket):
#         key = f"{merchantId}:{storeId}"
#         if key in self.active_connections:
#             self.active_connections[key].remove(websocket)
#             if not self.active_connections[key]:
#                 del self.active_connections[key]

#     async def send_personal_message(self, message: str, merchantId: int, storeId: int):
#         key = f"{merchantId}:{storeId}"
#         if key in self.active_connections:
#             for connection in self.active_connections[key]:
#                 await connection.send_text(message)

#     async def broadcast(self, message: str, merchantId: int, storeId: int):
#         key = f"{merchantId}:{storeId}"
#         if key in self.active_connections:
#             for connection in self.active_connections[key]:
#                 await connection.send_text(message)

# manager = ConnectionManager()

# @router.websocket('/ws/chat/{token}')
# async def websocket_endpoint(websocket: WebSocket, db: db_dependency, token:str):
#     decoded_token = decode_token(token)
#     if isinstance(decoded_token, JSONResponse):
#         return decoded_token
#     #print(decoded_token)
#     clientId = decoded_token.get('userId')
#     # if userType != "userId":
#     #     return JSONResponse(status_code=403, content={"detail": "you lack  privilages"})
#     await manager.connect(websocket,clientId)
#     while True:
#         try:
       
#             while redis_client.llen(f"messages:{clientId}") > 0:
#                 queued_message = json.loads(redis_client.lpop(f"messages:{clientId}"))
#                 await manager.send_personal_message(queued_message['message'], clientId) #f"Client {queued_message['sender_id']} says: {
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
#             message = message_data.get("message")
#             receiverId = int(message_data.get("id"))
           
#             new_message = messageTable(message=message, senderId=clientId, receiverId=receiverId)
#             db.add(new_message)
#             db.commit()
#             # Send personal message to the sender
#             await manager.send_personal_message(f"You wrote: {message}", clientId)
#             # Broadcast message to other clients
#             await manager.broadcast(f"Client {clientId} says: {message}", clientId,receiverId)
#         except WebSocketDisconnect:
#             manager.disconnect(clientId)
#             await manager.broadcast(f"Client {clientId} has left the chat", clientId,receiverId)
#             break


# @router.websocket('/ws/newchat/{token}/{storeId}')
# async def websocket_endpoint(websocket: WebSocket, db: db_dependency, token: str, storeId: int):
#     decoded_token = decode_token(token)
#     if isinstance(decoded_token, JSONResponse):
#         return decoded_token

#     clientId = decoded_token.get('userId')
#     # merchantId = decoded_token.get('merchantId')

#     # Validate if the store belongs to the merchant
#     # store = db.query(StoreTable).filter_by(id=storeId, merchantId=merchantId).first()
#     # if not store:
#     #     await websocket.close(code=1008, reason="Unauthorized access to this store")
#     #     return

#     # Connect WebSocket to the specific store
#     await manager.connect(websocket, clientId, storeId)

#     try:
#         while True:
#             # Handle queued messages for this store
#             while redis_client.llen(f"messages:{clientId}:{storeId}") > 0:
#                 queued_message = json.loads(redis_client.lpop(f"messages:{clientId}:{storeId}"))
#                 await manager.send_personal_message(queued_message['message'], clientId, storeId)

#             # Receive new message
#             data = await websocket.receive_text()
#             message_data = json.loads(data)

#             message = message_data.get("message")
#             targetStoreId = message_data.get("storeId")

#             # Save the message
#             new_message = messageTable(
#                 message=message,
#                 senderId=clientId,
#                 receiverId=clientId,
#                 storeId=targetStoreId
#             )
#             db.add(new_message)
#             db.commit()
#             await manager.broadcast(f"Client {clientId} has left the chat", clientId,receiverId)
#             # Notify the store
#             # await manager.send_personal_message(f"Client {clientId} says: {message}", clientId, targetStoreId)

#     except WebSocketDisconnect:
#         manager.disconnect(clientId, storeId, websocket)
#     except Exception as e:
#         print(f"Error: {e}")
#         await websocket.close(code=1011, reason="Internal Server Error")


# class myconnectionManager:
    
#     def __init__(self):
#         self.activeconnections: Dict[str, WebSocket] = {}

#     async def connect(self, websocket: WebSocket, clientId:int):
#         await websocket.accept()
#         self.activeconnections[clientId] = websocket
        
         
    
#     def disconnect(self, client_id: int):
#         del self.activeconnections[client_id]
   
#     async def send_personal_message(self, message: str, client_id: int):
#         websocket = self.activeconnections.get(client_id)
#         if websocket:
#             await websocket.send_text(message)
    
#     async def broadcast(self, message: str, senderId: int, recieverId: int):
#         receiver_ws = self.activeconnections.get(recieverId)
#         if receiver_ws:
#             await receiver_ws.send_text(message)
#         else:
#             # If the receiver is not connected, push the message to Redis
#             redis_client.rpush(f"messages:{recieverId}", json.dumps({
#                 'sender_id': senderId,
#                 'message': message
#             }))
#         # for clientId,connection in self.activeconnections.items():
#         #     if clientId != senderId and clientId == recieverId:
#         #         await connection.send_text(message)


manager = connectionManager()


#out of respect to php i created a unique connection id with concatenating userid and store id with dollar

@router.websocket('/ws/chat/{token}/{storeId}')
async def websocket_endpoint(websocket: WebSocket, db: db_dependency, token:str, storeId:int):
    decoded_token = decode_token(token)
    if isinstance(decoded_token, JSONResponse):
        return decoded_token
    # print(decoded_token)
    clientId = decoded_token.get('userId')
    # userType = decoded_token.get('userType')
    connectionId = str(clientId) + "$" + str(storeId)
   
    await manager.connect(websocket,connectionId)
    while True:
        try:
       
            while redis_client.llen(f"messages:{connectionId}") > 0:
                queued_message = json.loads(redis_client.lpop(f"messages:{connectionId}"))
                await manager.send_personal_message(queued_message['message'], connectionId) #f"Client {queued_message['sender_id']} says: {
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message")
            receiverId = int(message_data.get("id"))
            receiverstoreId = int(message_data.get("receiverstoreId"))
            receiverConnectionId = str(receiverId) + "$" + str(receiverstoreId)
            # print(receiverConnectionId)
            # print(connectionId)
            sendmessage = ({
            "message":message,"clientconnectionId": connectionId,"receiverconnectionId": receiverConnectionId
        })
            new_message = messageTable(message=message, senderId=connectionId, receiverId=receiverId, storeId= storeId, receiverStoreId= receiverstoreId,jsonMessage= sendmessage,clientconnectionId=connectionId, receiverconnectionId=receiverConnectionId)
            db.add(new_message)
            db.commit()
            # Send personal message to the sender
            await manager.send_personal_message(sendmessage, connectionId)
            # Broadcast message to other clients
            await manager.broadcast(sendmessage, connectionId,receiverConnectionId)
        except WebSocketDisconnect:
            manager.disconnect(connectionId)
            sendmessage = ({
            "message":f"Client {connectionId} has left the chat","senderconnectionId": connectionId,"receiverconnectionId": receiverConnectionId
        })
            await manager.broadcast(sendmessage, connectionId,receiverConnectionId)
            break


async def send_message_fun(db,message:str,clientId:int,receiverId:int,userstoreId,receiverstoreId,orderId:int):
    try:
        clientconnectionId = str(clientId) + "$" + str(userstoreId)
        receiverconnectionId = str(receiverId) + "$" + str(receiverstoreId)
        

        message.update({
            'clientconnectionId':clientconnectionId, 'receiverconnectionId':receiverconnectionId
        })

        newnotificaton = Notification(message=message['message'], sendFrom=clientId, receiverId=receiverId,senderStoreId=userstoreId, receiverIdStoreId=receiverstoreId,orderId=orderId,jsonMessage= message,clientconnectionId=clientconnectionId, receiverconnectionId=receiverconnectionId)
        db.add(newnotificaton)
        db.commit()
        
        await manager.send_personal_message(message, clientconnectionId)
        await manager.broadcast(message,clientconnectionId,receiverconnectionId)
    except Exception as e:
        print(e)  
        return JSONResponse(status_code=400, content={"detail": "unable to place order"})
    

async def notify(message,clientId,recieverId):
    await manager.broadcast(message, clientId, recieverId)

async def sentPersonal(message,clientId):
    await manager.send_personal_message(message,clientId)
    # print (clientId)


async def notifyperson(db,message,receiverId,receiverstoreId,orderId):
    
    receiverconnectionId = str(receiverId) + "$" + str(receiverstoreId)
    newnotificaton = Notification(message=message['message'], receiverId=receiverId, receiverIdStoreId=receiverstoreId,orderId=orderId,jsonMessage= message, receiverconnectionId=receiverconnectionId)
    db.add(newnotificaton)
    db.commit()

    await manager.send_personal_message(message,receiverconnectionId)