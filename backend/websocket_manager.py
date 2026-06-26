import json
from typing import Set, Dict
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # role -> set of websocket connections
        self.connections: Dict[str, Set[WebSocket]] = {
            "guest": set(),
            "chef": set(),
        }

    async def connect(self, ws: WebSocket, role: str):
        await ws.accept()
        role = role if role in self.connections else "guest"
        self.connections[role].add(ws)
        print(f"[WS] {role} 已连接 (共 {len(self.connections[role])} 个 {role})")

    def disconnect(self, ws: WebSocket, role: str):
        role = role if role in self.connections else "guest"
        self.connections[role].discard(ws)
        print(f"[WS] {role} 已断开 (剩余 {len(self.connections[role])} 个 {role})")

    async def broadcast_to_role(self, role: str, message: dict):
        """向指定角色的所有客户端广播消息"""
        if role not in self.connections:
            return
        dead = set()
        for ws in self.connections[role]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        self.connections[role] -= dead

    async def broadcast_to_all(self, message: dict):
        """向所有客户端广播"""
        for role in self.connections:
            await self.broadcast_to_role(role, message)


manager = ConnectionManager()
