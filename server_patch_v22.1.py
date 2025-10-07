"""
Genesis Resurrection Engine v22.1 - 긴급 패치
주요 수정사항:
1. 엔디안 통일 (빅 → 리틀)
2. 0x8B 패킷 구현
3. 0x86 좌표 시스템 수정
4. 에러 처리 강화
"""

import asyncio
import struct
import time
import random
from enum import Enum, auto
from typing import Optional, Tuple, Dict

# --- 로깅 모듈 (수정 없음) ---

class Logger:
    try:
        import colorama
        colorama.init(autoreset=True)
        C = {
            "INFO": colorama.Fore.CYAN,
            "DEBUG": colorama.Fore.WHITE,
            "ERROR": colorama.Fore.RED,
            "WARN": colorama.Fore.YELLOW,
            "SUCCESS": colorama.Fore.LIGHTGREEN_EX,
            "RX": colorama.Fore.LIGHTYELLOW_EX,
            "TX": colorama.Fore.LIGHTGREEN_EX,
            "SERVER": colorama.Fore.MAGENTA,
            "RESET": colorama.Style.RESET_ALL,
            "DATA": colorama.Fore.WHITE,
            "OPCODE_NAME": colorama.Fore.LIGHTWHITE_EX,
            "FIELD_NAME": colorama.Fore.CYAN,
            "VALUE_NUM": colorama.Fore.GREEN,
            "VALUE_STR": colorama.Fore.WHITE,
            "UNKNOWN": colorama.Fore.LIGHTMAGENTA_EX,
        }
    except ImportError:
        C = {k: "" for k in ["INFO", "DEBUG", "ERROR", "WARN", "SUCCESS", "RX", "TX", "SERVER", "RESET", "DATA", "OPCODE_NAME", "FIELD_NAME", "VALUE_NUM", "VALUE_STR", "UNKNOWN"]}

    @staticmethod
    def log(level, server_name, message):
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {Logger.C.get(level, '')}[{level.upper()}]{Logger.C['RESET']} {Logger.C['SERVER']}[{server_name}]{Logger.C['RESET']} {message}")

    @staticmethod
    def hexdump(data: bytes, length=16) -> str:
        if not data:
            return "  (empty payload)"
        lines = ["  --- Hexdump ---"]
        for i in range(0, len(data), length):
            chunk = data[i : i + length]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"  {Logger.C['DATA']}{i:04x}: {hex_part:<{length*3-1}}  |{text_part}|{Logger.C['RESET']}")
        return "\n".join(lines)


# --- 프로토콜 명세 ---

class Opcodes(Enum):
    C2S_AUTH_PING = 0x27
    S2C_AUTH_PONG = 0x27
    C2S_AUTH_LOGIN = 0x21
    S2C_AUTH_LOGIN_SUCCESS = 0x21
    C2S_AUTH_AVATAR_LIST_REQ = 0x29
    S2C_AUTH_AVATAR_LIST_RESP = 0x29
    C2S_AUTH_GAME_START = 0x28
    S2C_AUTH_GAME_START_RESP = 0x28
    C2S_GAME_HANDSHAKE = 0x24
    S2C_GAME_HANDSHAKE_ACK = 0x24
    S2C_WORLD_CREATE = 0x86
    S2C_CHARACTER_CREATE = 0x8B
    S2C_INVENTORY_INFO = 0x99
    S2C_FRIEND_LIST = 0x85
    C2S_LOADING_COMPLETE = 0xA3
    S2C_LOADING_ACK = 0xA3


OPCODE_NAMES = {op.value: op.name for op in Opcodes}


# --- 유틸리티 함수 (신규) ---

def encode_euckr_fixed(text: str, length: int = 21) -> bytes:
    """고정 길이 EUC-KR 문자열 인코딩"""
    encoded = text.encode("euc-kr", errors="replace")
    if len(encoded) > length:
        encoded = encoded[:length]
    return encoded.ljust(length, b"\x00")


def decode_euckr_fixed(data: bytes, length: int = 21) -> str:
    """고정 길이 EUC-KR 문자열 디코딩"""
    return data[:length].rstrip(b"\x00").decode("euc-kr", errors="replace")


# --- 패킷 디섹터 (엔디안 수정) ---

class PacketDissector:
    C = Logger.C

    @staticmethod
    def _dissect_c2s_auth_login(p):
        user = decode_euckr_fixed(p[0:16], 16)
        pwd = decode_euckr_fixed(p[16:32], 16)
        return (
            f"[{PacketDissector.C['FIELD_NAME']}user:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_STR']}'{user}'{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['FIELD_NAME']}pass:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_STR']}'{pwd}'{PacketDissector.C['RESET']}]"
        )

    @staticmethod
    def _dissect_c2s_game_handshake(p):
        if len(p) < 4:
            return "[Invalid handshake]"
        key = struct.unpack("<I", p[:4])[0]
        return (
            f"[{PacketDissector.C['FIELD_NAME']}session_key:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_NUM']}0x{key:08X}{PacketDissector.C['RESET']}]"
        )

    @staticmethod
    def _dissect_s2c_auth_game_start_resp(p):
        if len(p) < 7:
            return "[Invalid game start]"
        flag = struct.unpack("<B", p[:1])[0]
        key = struct.unpack("<I", p[1:5])[0]
        ip_end = p.find(b"\x00", 5)
        if ip_end == -1:
            ip_end = len(p) - 2
        ip_raw = p[5:ip_end]
        port = struct.unpack("<H", p[-2:])[0]
        ip = decode_euckr_fixed(ip_raw, len(ip_raw))
        return (
            f"[{PacketDissector.C['FIELD_NAME']}key:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_NUM']}0x{key:08X}{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['FIELD_NAME']}ip:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_STR']}'{ip}'{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['FIELD_NAME']}port:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_NUM']}{port}{PacketDissector.C['RESET']}]"
        )

    @staticmethod
    def _dissect_s2c_world_create(p):
        if len(p) < 15:
            return "[Invalid world data]"
        flag, map_id, px, py, cc, ic, ec = struct.unpack("<bHiiHHH", p[:15])
        tile_x, pixel_x = divmod(px, 800)
        tile_y, pixel_y = divmod(py, 600)
        return (
            f"[{PacketDissector.C['FIELD_NAME']}map:{PacketDissector.C['RESET']}"
            f"{PacketDissector.C['VALUE_NUM']}{map_id}{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['FIELD_NAME']}pos:{PacketDissector.C['RESET']}"
            f"{PacketDissector.C['VALUE_NUM']}tile({tile_x},{tile_y})+px({pixel_x},{pixel_y}){PacketDissector.C['RESET']} "
            f"{PacketDissector.C['FIELD_NAME']}entities:{PacketDissector.C['RESET']}"
            f"{PacketDissector.C['VALUE_NUM']}C{cc}/I{ic}/E{ec}{PacketDissector.C['RESET']}]"
        )

    @staticmethod
    def _dissect_s2c_loading_ack(p):
        if len(p) < 2:
            return "[Invalid]"
        sub_cmd = struct.unpack("<H", p[:2])[0]
        return (
            f"[{PacketDissector.C['FIELD_NAME']}sub_cmd:{PacketDissector.C['RESET']} "
            f"{PacketDissector.C['VALUE_NUM']}0x{sub_cmd:X}{PacketDissector.C['RESET']}]"
        )

    dissectors = {
        0x21: _dissect_c2s_auth_login.__func__,
        0x24: _dissect_c2s_game_handshake.__func__,
        0x28: _dissect_s2c_auth_game_start_resp.__func__,
        0x86: _dissect_s2c_world_create.__func__,
        0xA3: _dissect_s2c_loading_ack.__func__,
    }

    @staticmethod
    def dissect(opcode, payload):
        if opcode in PacketDissector.dissectors:
            try:
                return PacketDissector.dissectors[opcode](payload)
            except (struct.error, IndexError) as e:
                return f"[{PacketDissector.C['ERROR']}Dissector Error:{PacketDissector.C['RESET']} {e}]"
        return f"({PacketDissector.C['UNKNOWN']}Unknown Structure{PacketDissector.C['RESET']})"


# --- 설정 및 데이터 구조 ---

class ServerConfig:
    AUTH_HOST, AUTH_PORT = "0.0.0.0", 6000
    GAME_IP = "112.212.253.137"
    GAME_HOST, GAME_PORT = "0.0.0.0", 7777
    DEBUG_MODE = True


# 세션 저장소 (간단한 in-memory, 추후 Redis 전환 가능)
SESSION_STORE: Dict[str, int] = {}


class Packet:
    @staticmethod
    def create(opcode: Opcodes, payload: bytes = b"") -> bytes:
        """패킷 생성 (리틀엔디안)"""
        # 헤더: [2바이트 길이(payload + opcode)] [1바이트 opcode] [payload]
        return struct.pack("<HB", len(payload) + 1, opcode.value) + payload

    @staticmethod
    def parse(data: bytes) -> Optional[Tuple[int, bytes, int]]:
        """패킷 파싱 (리틀엔디안)"""
        if len(data) < 3:
            return None
        
        try:
            p_len = struct.unpack("<H", data[:2])[0]
            
            # 길이 검증
            if p_len < 1 or p_len > 65530:
                Logger.log("ERROR", "PACKET", f"비정상 패킷 길이: {p_len}")
                return None
            
            pkt_len = 2 + p_len
            
            if len(data) < pkt_len:
                return None
            
            opcode = data[2]
            payload = data[3:pkt_len]
            
            return opcode, payload, pkt_len
            
        except struct.error as e:
            Logger.log("ERROR", "PACKET", f"파싱 오류: {e}")
            return None


class ClientFlow(Enum):
    AWAITING_PING = auto()
    AWAITING_LOGIN = auto()
    LOGGED_IN_MENU = auto()
    AVATAR_SCREEN = auto()
    AWAITING_HANDSHAKE = auto()
    AWAITING_READY_SIGNAL = auto()
    IN_WORLD = auto()


# --- 서버 구현 (강화된 에러 처리) ---

class BaseServer:
    SERVER_NAME = "BASE"
    INITIAL_STATE = None

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info("peername")
        state = self.INITIAL_STATE
        buffer = b""
        
        Logger.log("INFO", self.SERVER_NAME, f"클라이언트 접속: {peer}")
        
        try:
            while True:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=60.0)
                except asyncio.TimeoutError:
                    Logger.log("WARN", self.SERVER_NAME, f"{peer} 타임아웃 (60초)")
                    break
                
                if not data:
                    Logger.log("INFO", self.SERVER_NAME, f"{peer} 연결 종료 (클라이언트)")
                    break
                
                buffer += data
                
                # 버퍼 크기 제한
                if len(buffer) > 1024 * 1024:
                    Logger.log("ERROR", self.SERVER_NAME, f"{peer} 버퍼 오버플로우!")
                    break
                
                while buffer:
                    parsed = Packet.parse(buffer)
                    if not parsed:
                        break
                    
                    opcode, payload, packet_len = parsed
                    
                    if packet_len > 65535:
                        Logger.log("ERROR", self.SERVER_NAME, f"비정상 패킷 크기: {packet_len}")
                        return
                    
                    try:
                        state = await self.route_packet(writer, state, opcode, payload)
                        if state is None:
                            Logger.log("INFO", self.SERVER_NAME, f"{peer} 세션 종료 요청")
                            return
                    except Exception as e:
                        Logger.log("ERROR", self.SERVER_NAME, f"패킷 처리 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        return
                    
                    buffer = buffer[packet_len:]
                    
        except (ConnectionResetError, asyncio.IncompleteReadError, BrokenPipeError) as e:
            Logger.log("INFO", self.SERVER_NAME, f"{peer} 연결 종료: {type(e).__name__}")
        except Exception as e:
            Logger.log("ERROR", self.SERVER_NAME, f"{peer} 예외 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass
            Logger.log("INFO", self.SERVER_NAME, f"{peer} 세션 정리 완료")

    async def send_packet(self, writer, opcode: Opcodes, payload: bytes = b""):
        op_name = OPCODE_NAMES.get(opcode.value, "UNKNOWN")
        details = PacketDissector.dissect(opcode.value, payload)
        Logger.log(
            "DEBUG",
            self.SERVER_NAME,
            f"{Logger.C['TX']}[S->C]{Logger.C['RESET']} Opcode(0x{opcode.value:02X} - {Logger.C['OPCODE_NAME']}{op_name}{Logger.C['RESET']}) {details}",
        )
        if ServerConfig.DEBUG_MODE and "Unknown" in details:
            Logger.log("DEBUG", self.SERVER_NAME, Logger.hexdump(payload))

        packet_to_send = Packet.create(opcode, payload)
        writer.write(packet_to_send)
        await writer.drain()

    async def route_packet(self, writer, state, opcode, payload):
        op_name = OPCODE_NAMES.get(opcode, "UNKNOWN")
        details = PacketDissector.dissect(opcode, payload)
        Logger.log(
            "DEBUG",
            self.SERVER_NAME,
            f"{Logger.C['RX']}[C->S]{Logger.C['RESET']} Opcode(0x{opcode:02X} - {Logger.C['OPCODE_NAME']}{op_name}{Logger.C['RESET']}) {details}",
        )
        if ServerConfig.DEBUG_MODE and "Unknown" in details:
            Logger.log("DEBUG", self.SERVER_NAME, Logger.hexdump(payload))
        return await self._internal_route(writer, state, opcode, payload)

    async def _internal_route(self, writer, state, opcode, payload):
        raise NotImplementedError


class AuthServer(BaseServer):
    SERVER_NAME = "AUTH"
    INITIAL_STATE = ClientFlow.AWAITING_PING

    def __init__(self):
        self.user_data = {
            "test": {
                "password": "1234",
                "avatars": [
                    {"id": 100001, "name": "Challenger", "level": 99, "job": 1}
                ]
            }
        }

    async def _internal_route(self, writer, state, opcode, payload):
        if state == ClientFlow.AWAITING_PING and opcode == Opcodes.C2S_AUTH_PING.value:
            await self.send_packet(writer, Opcodes.S2C_AUTH_PONG)
            return ClientFlow.AWAITING_LOGIN
        
        elif state == ClientFlow.AWAITING_LOGIN and opcode == Opcodes.C2S_AUTH_LOGIN.value:
            # 로그인 검증 (간단한 버전)
            username = decode_euckr_fixed(payload[0:16], 16)
            password = decode_euckr_fixed(payload[16:32], 16)
            
            if username in self.user_data and self.user_data[username]["password"] == password:
                Logger.log("SUCCESS", self.SERVER_NAME, f"로그인 성공: {username}")
                await self.send_packet(writer, Opcodes.S2C_AUTH_LOGIN_SUCCESS, b"\x01" + b"\x00" * 498)
                return ClientFlow.LOGGED_IN_MENU
            else:
                Logger.log("WARN", self.SERVER_NAME, f"로그인 실패: {username}")
                await self.send_packet(writer, Opcodes.S2C_AUTH_LOGIN_SUCCESS, b"\x00" + b"\x00" * 498)
                return state
        
        elif state == ClientFlow.LOGGED_IN_MENU and opcode == Opcodes.C2S_AUTH_AVATAR_LIST_REQ.value:
            await self.send_avatar_list(writer)
            return ClientFlow.AVATAR_SCREEN
        
        elif state == ClientFlow.AVATAR_SCREEN and opcode == Opcodes.C2S_AUTH_GAME_START.value:
            await self.handle_game_start(writer)
            return None
        
        return state

    async def send_avatar_list(self, writer):
        # 하드코딩된 캐릭터 목록 (추후 DB 연동)
        avatars = self.user_data["test"]["avatars"]
        p = bytearray()
        
        # 캐릭터 수 (리틀엔디안)
        p += struct.pack("<B", len(avatars))
        
        for i, av in enumerate(avatars):
            p += struct.pack("<B", i + 1)  # 슬롯 번호
            p += encode_euckr_fixed(av["name"])  # 21바이트
            p += struct.pack("<BB", av["level"], av["job"])
            p += b"\x00" * 20  # 추가 데이터
        
        await self.send_packet(writer, Opcodes.S2C_AUTH_AVATAR_LIST_RESP, bytes(p))

    async def handle_game_start(self, writer):
        key = random.randint(0x10000000, 0xFFFFFFFF)
        peer = writer.get_extra_info("peername")
        
        # 세션 키 저장 (IP 기반)
        SESSION_STORE[peer[0]] = key
        Logger.log("INFO", self.SERVER_NAME, f"세션 키 발급: {peer[0]} -> 0x{key:08X}")
        
        p = bytearray()
        p += struct.pack("<B", 1)  # 성공 플래그
        p += struct.pack("<I", key)  # 세션 키 (리틀엔디안)
        p += ServerConfig.GAME_IP.encode("euc-kr")
        p += b"\x00"
        p += struct.pack("<H", ServerConfig.GAME_PORT)  # 포트 (리틀엔디안)
        
        await self.send_packet(writer, Opcodes.S2C_AUTH_GAME_START_RESP, bytes(p))


class GameServer(BaseServer):
    SERVER_NAME = "GAME"
    INITIAL_STATE = ClientFlow.AWAITING_HANDSHAKE

    async def _internal_route(self, writer, state, opcode, payload):
        if state == ClientFlow.AWAITING_HANDSHAKE and opcode == Opcodes.C2S_GAME_HANDSHAKE.value:
            # 세션 키 검증
            if len(payload) < 4:
                Logger.log("ERROR", self.SERVER_NAME, "핸드셰이크 페이로드 부족")
                return None
            
            received_key = struct.unpack("<I", payload[:4])[0]
            peer = writer.get_extra_info("peername")
            
            expected_key = SESSION_STORE.get(peer[0])
            
            if expected_key is None:
                Logger.log("ERROR", self.SERVER_NAME, f"세션 키 없음: {peer[0]}")
                return None
            
            if expected_key != received_key:
                Logger.log("ERROR", self.SERVER_NAME, f"세션 키 불일치! 예상:0x{expected_key:08X} 수신:0x{received_key:08X}")
                return None
            
            Logger.log("SUCCESS", self.SERVER_NAME, f"세션 키 검증 성공: 0x{received_key:08X}")
            
            # 월드 데이터 전송 시작
            asyncio.create_task(self.send_world_blueprints(writer))
            
            return ClientFlow.AWAITING_READY_SIGNAL
        
        elif state == ClientFlow.AWAITING_READY_SIGNAL and opcode == Opcodes.C2S_LOADING_COMPLETE.value:
            Logger.log("SUCCESS", self.SERVER_NAME, f"로딩 완료 신호(0xA3) 수신!")
            
            # 최종 승인 (서브커맨드 0x131)
            final_approval = struct.pack("<H", 0x131)
            await self.send_packet(writer, Opcodes.S2C_LOADING_ACK, final_approval)
            
            Logger.log("SUCCESS", self.SERVER_NAME, f"월드 진입 완료! 클라이언트가 게임을 시작합니다.")
            return ClientFlow.IN_WORLD
        
        Logger.log("WARN", self.SERVER_NAME, f"프로토콜 위반: 상태({state.name})에서 Opcode(0x{opcode:02X})")
        return state

    async def send_world_blueprints(self, writer):
        try:
            # 1. 핸드셰이크 ACK
            await self.send_packet(writer, Opcodes.S2C_GAME_HANDSHAKE_ACK, struct.pack("<H", 1))
            await asyncio.sleep(0.1)

            # 2. 월드 생성 (0x86) - 좌표 시스템 수정
            flag = 0
            map_id = 1  # 시작 맵
            
            # 좌표: 타일(5, 5)의 중앙
            start_tile_x, start_tile_y = 5, 5
            px = start_tile_x * 800 + 400  # 픽셀 X
            py = start_tile_y * 600 + 300  # 픽셀 Y
            
            char_count = 0  # 주변 캐릭터
            item_count = 0  # 바닥 아이템
            effect_count = 0  # 이펙트
            
            world_payload = struct.pack("<bHiiHHH", flag, map_id, px, py, char_count, item_count, effect_count)
            await self.send_packet(writer, Opcodes.S2C_WORLD_CREATE, world_payload)
            await asyncio.sleep(0.1)

            # 3. 내 캐릭터 정보 (0x8B) - 필수 구현!
            char_payload = bytearray()
            
            # v23 = 1 (기본 모드, 장비 정보 없이)
            char_payload += struct.pack("<B", 1)
            
            # 캐릭터 ID (this + 1768)
            char_payload += struct.pack("<I", 100001)
            
            # 캐릭터 이름 (this + 1799, 21바이트)
            char_payload += encode_euckr_fixed("Challenger", 21)
            
            # 기본 스탯 (this + 1960, this + 1772)
            char_payload += struct.pack("<B", 0)  # 기타 플래그
            char_payload += struct.pack("<B", 0)  # 상태 플래그
            
            await self.send_packet(writer, Opcodes.S2C_CHARACTER_CREATE, bytes(char_payload))
            await asyncio.sleep(0.1)

            # 4. 인벤토리 정보 (0x99)
            inv_payload = bytearray()
            inv_payload += struct.pack("<H", 0)  # 시간 값
            inv_payload += struct.pack("<H", 0)  # 아이템 개수 (빈 인벤토리)
            
            await self.send_packet(writer, Opcodes.S2C_INVENTORY_INFO, bytes(inv_payload))
            
            Logger.log("INFO", self.SERVER_NAME, "월드 설계도 전송 완료. 클라이언트 로딩 대기 중...")
            
        except Exception as e:
            Logger.log("ERROR", self.SERVER_NAME, f"월드 설계도 전송 오류: {e}")
            import traceback
            traceback.print_exc()


async def main():
    Logger.log("INFO", "SYSTEM", "=" * 60)
    Logger.log("INFO", "SYSTEM", "Genesis Resurrection Engine v22.1 - PATCHED")
    Logger.log("INFO", "SYSTEM", "주요 수정사항:")
    Logger.log("INFO", "SYSTEM", "  - 엔디안 통일 (빅 -> 리틀)")
    Logger.log("INFO", "SYSTEM", "  - 0x8B 패킷 구현 (캐릭터 정보)")
    Logger.log("INFO", "SYSTEM", "  - 0x86 좌표 시스템 수정 (800x600 타일)")
    Logger.log("INFO", "SYSTEM", "  - 세션 키 검증 추가")
    Logger.log("INFO", "SYSTEM", "  - 에러 처리 강화")
    Logger.log("INFO", "SYSTEM", "=" * 60)
    
    auth = AuthServer()
    game = GameServer()
    
    server_auth = await asyncio.start_server(
        auth.handle_client, ServerConfig.AUTH_HOST, ServerConfig.AUTH_PORT
    )
    server_game = await asyncio.start_server(
        game.handle_client, ServerConfig.GAME_HOST, ServerConfig.GAME_PORT
    )
    
    Logger.log("SUCCESS", "SYSTEM", f"인증 서버: {server_auth.sockets[0].getsockname()}")
    Logger.log("SUCCESS", "SYSTEM", f"게임 서버: {server_game.sockets[0].getsockname()}")
    Logger.log("INFO", "SYSTEM", f"게임 서버 공인 IP: {ServerConfig.GAME_IP}")
    Logger.log("INFO", "SYSTEM", "서버 준비 완료. 클라이언트 접속 대기 중...")
    
    async with server_auth, server_game:
        await asyncio.gather(server_auth.serve_forever(), server_game.serve_forever())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        Logger.log("INFO", "SYSTEM", "서버 종료 (Ctrl+C)")