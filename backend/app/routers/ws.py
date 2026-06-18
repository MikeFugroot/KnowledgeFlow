# -*- coding: utf-8 -*-
"""
WebSocket 路由 — /ws 实时通信

消息格式：{type, payload, timestamp}
支持：task_progress, log, index_status, profile_status, task_completed, task_failed, ping, pong
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._connection_ids: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        conn_id = f"ws_{id(websocket)}"
        self._connection_ids[websocket] = conn_id

    def disconnect(self, websocket: WebSocket) -> None:
        """断开连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self._connection_ids.pop(websocket, None)

    async def broadcast(self, msg_type: str, payload: dict) -> None:
        """广播消息给所有连接"""
        if not self.active_connections:
            return

        message = {
            "type": msg_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to(self, websocket: WebSocket, msg_type: str, payload: dict) -> None:
        """发送消息给指定连接"""
        message = {
            "type": msg_type,
            "payload": payload,
            "timestamp": datetime.now().isoformat(),
        }
        try:
            await websocket.send_json(message)
        except Exception:
            self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        """当前连接数"""
        return len(self.active_connections)


# 全局连接管理器
ws_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket 端点"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type", "")

                # 处理心跳
                if msg_type == "ping":
                    await ws_manager.send_to(websocket, "pong", {})
                else:
                    # 其他消息暂不处理，返回确认
                    await ws_manager.send_to(
                        websocket, "ack",
                        {"original_type": msg_type},
                    )
            except json.JSONDecodeError:
                await ws_manager.send_to(
                    websocket, "error",
                    {"message": "无效的 JSON 格式"},
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
