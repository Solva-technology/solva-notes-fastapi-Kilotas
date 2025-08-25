from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from app.chat.manager import manager
from app.core.templates import templates

router = APIRouter()


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@router.websocket("/ws/anon-chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        data = await websocket.receive_json()
        nickname = (data.get("nickname") or "").strip()
        if not nickname:
            await websocket.close(code=1008, reason="Nickname required")
            return

        await manager.connect(websocket, nickname)

        while True:
            data = await websocket.receive_json()
            message_text = (data.get("text") or "").strip()
            if message_text:
                await manager.handle_user_message(websocket, message_text)

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
