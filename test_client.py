#!/usr/bin/env python3
"""
간단한 테스트 클라이언트 - 서버 응답 검증용
"""

import socket
import struct
import time

class TestClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None
    
    def connect(self):
        print(f"[연결] {self.host}:{self.port}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5.0)
        self.sock.connect((self.host, self.port))
        print("[성공] 연결됨")
    
    def send_packet(self, opcode, payload=b""):
        packet = struct.pack("<HB", len(payload) + 1, opcode) + payload
        print(f"[송신] Opcode=0x{opcode:02X}, 길이={len(payload)+1}")
        self.sock.sendall(packet)
    
    def recv_packet(self):
        # 헤더 읽기
        header = self.sock.recv(3)
        if len(header) < 3:
            print("[오류] 헤더 수신 실패")
            return None, None
        
        p_len = struct.unpack("<H", header[:2])[0]
        opcode = header[2]
        
        # 페이로드 읽기
        payload = b""
        if p_len > 1:
            payload = self.sock.recv(p_len - 1)
        
        print(f"[수신] Opcode=0x{opcode:02X}, 길이={p_len}")
        return opcode, payload
    
    def close(self):
        if self.sock:
            self.sock.close()
            print("[종료] 연결 종료")
    
    def hexdump(self, data, label=""):
        if label:
            print(f"[{label}]")
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            text_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print(f"  {i:04x}: {hex_part:<48}  |{text_part}|")


def test_auth_server():
    """인증 서버 테스트"""
    print("\n" + "="*60)
    print("인증 서버 테스트 시작")
    print("="*60)
    
    client = TestClient("127.0.0.1", 6000)
    
    try:
        # 1. 연결
        client.connect()
        time.sleep(0.5)
        
        # 2. PING
        print("\n[단계 1] PING 전송 (0x27)")
        client.send_packet(0x27)
        opcode, payload = client.recv_packet()
        if opcode == 0x27:
            print("✅ PONG 수신 성공")
        else:
            print(f"❌ 예상: 0x27, 실제: 0x{opcode:02X}")
        
        time.sleep(0.5)
        
        # 3. 로그인
        print("\n[단계 2] 로그인 전송 (0x21)")
        username = b"test".ljust(16, b"\x00")
        password = b"1234".ljust(16, b"\x00")
        login_payload = username + password
        client.send_packet(0x21, login_payload)
        
        opcode, payload = client.recv_packet()
        if opcode == 0x21:
            success = payload[0] if len(payload) > 0 else 0
            if success == 1:
                print("✅ 로그인 성공")
            else:
                print("❌ 로그인 실패")
            client.hexdump(payload[:20], "응답 데이터")
        
        time.sleep(0.5)
        
        # 4. 캐릭터 목록
        print("\n[단계 3] 캐릭터 목록 요청 (0x29)")
        client.send_packet(0x29)
        
        opcode, payload = client.recv_packet()
        if opcode == 0x29:
            char_count = payload[0] if len(payload) > 0 else 0
            print(f"✅ 캐릭터 수: {char_count}")
            client.hexdump(payload[:50], "캐릭터 데이터")
        
        time.sleep(0.5)
        
        # 5. 게임 시작
        print("\n[단계 4] 게임 시작 (0x28)")
        client.send_packet(0x28, b"\x01")  # 슬롯 1
        
        opcode, payload = client.recv_packet()
        if opcode == 0x28:
            if len(payload) >= 7:
                flag = payload[0]
                session_key = struct.unpack("<I", payload[1:5])[0]
                ip_end = payload.find(b"\x00", 5)
                ip = payload[5:ip_end].decode("euc-kr", errors="ignore")
                port = struct.unpack("<H", payload[-2:])[0]
                
                print(f"✅ 게임 서버 정보:")
                print(f"   세션 키: 0x{session_key:08X}")
                print(f"   IP: {ip}")
                print(f"   포트: {port}")
                
                return session_key, ip, port
            else:
                print("❌ 응답 데이터 부족")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    return None, None, None


def test_game_server(session_key):
    """게임 서버 테스트"""
    print("\n" + "="*60)
    print("게임 서버 테스트 시작")
    print("="*60)
    
    client = TestClient("127.0.0.1", 7777)
    
    try:
        # 1. 연결
        client.connect()
        time.sleep(0.5)
        
        # 2. 핸드셰이크
        print(f"\n[단계 1] 핸드셰이크 (0x24) - 세션 키: 0x{session_key:08X}")
        handshake_payload = struct.pack("<I", session_key)
        client.send_packet(0x24, handshake_payload)
        
        # 3. 월드 데이터 수신 (여러 패킷)
        print("\n[단계 2] 월드 데이터 수신 대기...")
        
        for i in range(10):  # 최대 10개 패킷
            try:
                opcode, payload = client.recv_packet()
                
                if opcode == 0x24:
                    print("✅ 핸드셰이크 ACK")
                
                elif opcode == 0x86:
                    print("✅ 월드 생성 (0x86)")
                    if len(payload) >= 15:
                        flag, map_id, px, py, cc, ic, ec = struct.unpack("<bHiiHHH", payload[:15])
                        tile_x, pixel_x = divmod(px, 800)
                        tile_y, pixel_y = divmod(py, 600)
                        print(f"   맵 ID: {map_id}")
                        print(f"   위치: 타일({tile_x},{tile_y}) + 픽셀({pixel_x},{pixel_y})")
                        print(f"   엔티티: 캐릭터{cc}/아이템{ic}/이펙트{ec}")
                
                elif opcode == 0x8B:
                    print("✅ 캐릭터 정보 (0x8B)")
                    if len(payload) >= 26:
                        version = payload[0]
                        char_id = struct.unpack("<I", payload[1:5])[0]
                        name = payload[5:26].rstrip(b"\x00").decode("euc-kr", errors="ignore")
                        print(f"   버전: {version}")
                        print(f"   ID: {char_id}")
                        print(f"   이름: {name}")
                    client.hexdump(payload, "캐릭터 데이터")
                
                elif opcode == 0x99:
                    print("✅ 인벤토리 (0x99)")
                    if len(payload) >= 4:
                        time_val, item_count = struct.unpack("<HH", payload[:4])
                        print(f"   아이템 수: {item_count}")
                
                time.sleep(0.3)
                
            except socket.timeout:
                print("   (타임아웃 - 더 이상 데이터 없음)")
                break
        
        # 4. 로딩 완료 신호
        print("\n[단계 3] 로딩 완료 신호 전송 (0xA3)")
        client.send_packet(0xA3, struct.pack("<H", 0))
        
        opcode, payload = client.recv_packet()
        if opcode == 0xA3:
            if len(payload) >= 2:
                sub_cmd = struct.unpack("<H", payload[:2])[0]
                print(f"✅ 최종 승인 수신 - 서브커맨드: 0x{sub_cmd:X}")
                if sub_cmd == 0x131:
                    print("🎉 게임 진입 성공!")
                else:
                    print(f"⚠️  예상치 못한 서브커맨드: 0x{sub_cmd:X}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()


def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║   Genesis Resurrection - 서버 테스트 클라이언트 v1.0      ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # 1. 인증 서버 테스트
    session_key, ip, port = test_auth_server()
    
    if session_key is None:
        print("\n❌ 인증 서버 테스트 실패. 게임 서버 테스트 건너뜀.")
        return
    
    time.sleep(1)
    
    # 2. 게임 서버 테스트
    test_game_server(session_key)
    
    print("\n" + "="*60)
    print("모든 테스트 완료!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트 중단 (Ctrl+C)")