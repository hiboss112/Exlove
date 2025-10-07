# Genesis Resurrection v22.0 → v22.1 패치 노트

## 🔴 긴급 수정사항

### 1. 엔디안 통일 (치명적 버그 수정)
**문제**: 클라이언트는 리틀엔디안을 사용하는데 서버가 빅엔디안 사용
**영향**: 모든 숫자 데이터 파싱 실패 → 게임 진입 불가

**수정 내용**:
```python
# Before (v22.0)
struct.pack(">HB", ...)  # 빅엔디안
struct.pack(">I", ...)

# After (v22.1)
struct.pack("<HB", ...)  # 리틀엔디안
struct.pack("<I", ...)
```

---

### 2. 0x8B 패킷 구현 (필수 패킷)
**문제**: 빈 패킷 전송으로 클라이언트가 캐릭터 정보 로드 실패

**구현 내용**:
```python
# v23 = 1 모드 (기본 정보만)
char_payload = bytearray()
char_payload += struct.pack("<B", 1)              # 버전 플래그
char_payload += struct.pack("<I", 100001)         # 캐릭터 ID
char_payload += encode_euckr_fixed("이름", 21)    # 이름 (21바이트)
char_payload += struct.pack("<B", 0)              # 기타 플래그
char_payload += struct.pack("<B", 0)              # 상태 플래그
```

**클라이언트 메모리 매핑**:
- `this + 1768`: 캐릭터 ID (dword)
- `this + 1799`: 캐릭터 이름 (21 bytes)
- `this + 1960`: 기타 플래그 (byte)
- `this + 1772`: 상태 플래그 (byte)

---

### 3. 0x86 좌표 시스템 수정
**문제**: 
1. 구조체 정의 오류 (`biiHHH` → `bHiiHHH`)
2. 모든 좌표가 0으로 설정되어 맵 로딩 실패

**수정 내용**:
```python
# Before
world_payload = struct.pack("<biiHHH", 0, 0, 0, 0, 0, 0)

# After
flag = 0
map_id = 1                          # 맵 ID (word)
px = 5 * 800 + 400                  # 절대 X 좌표
py = 5 * 600 + 300                  # 절대 Y 좌표
char_count = 0
item_count = 0
effect_count = 0

world_payload = struct.pack("<bHiiHHH", flag, map_id, px, py, 
                            char_count, item_count, effect_count)
```

**좌표 시스템 설명**:
```
타일 좌표 → 절대 좌표 변환:
  절대X = 타일X × 800 + 픽셀오프셋X (0-799)
  절대Y = 타일Y × 600 + 픽셀오프셋Y (0-599)

예시: 타일(5,5)의 중앙
  절대X = 5 × 800 + 400 = 4400
  절대Y = 5 × 600 + 300 = 3300
```

---

## 🟡 중요 개선사항

### 4. 세션 키 검증 추가
**보안 강화**: 인증 서버와 게임 서버 간 세션 검증

```python
# AuthServer: 세션 키 발급
key = random.randint(0x10000000, 0xFFFFFFFF)
SESSION_STORE[client_ip] = key

# GameServer: 세션 키 검증
received_key = struct.unpack("<I", payload[:4])[0]
if SESSION_STORE.get(client_ip) != received_key:
    # 세션 거부
```

---

### 5. 에러 처리 강화

**타임아웃 추가**:
```python
data = await asyncio.wait_for(reader.read(4096), timeout=60.0)
```

**버퍼 오버플로우 방지**:
```python
if len(buffer) > 1024 * 1024:  # 1MB 제한
    Logger.log("ERROR", "버퍼 오버플로우!")
    break
```

**패킷 크기 검증**:
```python
if p_len < 1 or p_len > 65530:
    Logger.log("ERROR", f"비정상 패킷 길이: {p_len}")
    return None
```

---

### 6. 문자열 처리 유틸리티

**고정 길이 EUC-KR 인코딩/디코딩**:
```python
def encode_euckr_fixed(text: str, length: int = 21) -> bytes:
    """고정 길이로 인코딩 + NULL 패딩"""
    encoded = text.encode("euc-kr", errors="replace")
    if len(encoded) > length:
        encoded = encoded[:length]
    return encoded.ljust(length, b"\x00")

def decode_euckr_fixed(data: bytes, length: int = 21) -> str:
    """고정 길이 디코딩 + NULL 제거"""
    return data[:length].rstrip(b"\x00").decode("euc-kr", errors="replace")
```

---

### 7. 디버그 모드 추가

```python
class ServerConfig:
    DEBUG_MODE = True  # False로 설정 시 hexdump 비활성화
```

---

## 📊 패킷 구조 정리

### 공통 패킷 헤더
```
[2 bytes] 페이로드 길이 (리틀엔디안)
[1 byte]  Opcode
[N bytes] Payload
```

### 0x86 - 월드 생성
```c
struct WorldCreate {
    int8_t   flag;          // 0
    uint16_t map_id;        // 1
    int32_t  absolute_x;    // 4400
    int32_t  absolute_y;    // 3300
    uint16_t char_count;    // 0
    uint16_t item_count;    // 0
    uint16_t effect_count;  // 0
};
```

### 0x8B - 캐릭터 정보 (v23=1 모드)
```c
struct CharacterInfo {
    uint8_t  version;       // 1
    uint32_t char_id;       // 100001
    char     name[21];      // "Challenger"
    uint8_t  misc_flag;     // 0
    uint8_t  state_flag;    // 0
};
```

### 0x99 - 인벤토리
```c
struct InventoryInfo {
    uint16_t time_value;    // 0
    uint16_t item_count;    // 0
    // Item[] items;
};

struct Item {
    uint32_t item_id;
    char     name[21];
    uint16_t quantity;
    uint8_t  flags;
    uint16_t item_type;
};
```

---

## 🧪 테스트 시나리오

### 최소 성공 경로
1. ✅ 클라이언트 연결 → AUTH 서버
2. ✅ PING/PONG (0x27)
3. ✅ 로그인 (0x21) - 성공
4. ✅ 캐릭터 목록 요청 (0x29)
5. ✅ 게임 시작 (0x28) - 세션 키 발급
6. ✅ 클라이언트 연결 → GAME 서버
7. ✅ 핸드셰이크 (0x24) - 세션 키 검증
8. ✅ 월드 데이터 수신:
   - 0x24 ACK
   - 0x86 월드 생성
   - 0x8B 캐릭터 정보
   - 0x99 인벤토리
9. ✅ 로딩 완료 신호 (0xA3)
10. ✅ 최종 승인 (0xA3, sub_cmd=0x131)
11. ✅ 게임 진입!

---

## 🚀 다음 버전 개발 목표 (v22.2)

### 필수 구현
- [ ] 0x8B v23=3 모드 (전체 장비 정보)
- [ ] 주변 엔티티 스폰 (0x86 확장)
- [ ] 이동 패킷 (클라이언트 → 서버)
- [ ] 채팅 시스템

### 인프라
- [ ] PostgreSQL/SQLite DB 연동
- [ ] Redis 세션 저장소
- [ ] 로그 파일 저장

### 게임 로직
- [ ] 맵 데이터 로더 (파일 기반)
- [ ] 아이템 데이터베이스
- [ ] NPC 스크립트 시스템

---

## 📝 개발자 노트

### 클라이언트 분석 결과와의 매핑

리버싱한 클라이언트 코드에서:

```c
// sub_4252D0 - UI/시스템 핸들러
case 0x8B:
    *(_DWORD *)(this + 1768) = sub_423920(a2);  // 캐릭터 ID
    sub_4239B0(this + 1799, 21);                // 이름 읽기
    *(_BYTE *)(this + 1960) = sub_423950(a2);   // 기타 플래그
    *(_BYTE *)(this + 1772) = sub_423950(a2);   // 상태 플래그

// sub_459790 - 월드/엔티티 핸들러  
case 0x86:
    flag = data[0];
    map_id = read_word(data[1:3]);
    px = read_dword(data[3:7]);
    py = read_dword(data[7:11]);
```

서버 구현이 이제 클라이언트 기대값과 **정확히 일치**합니다!

---

## ⚠️ 알려진 제한사항

1. **인메모리 세션**: 서버 재시작 시 세션 소멸
2. **단일 맵**: 맵 ID 1만 지원
3. **하드코딩된 데이터**: DB 미연동
4. **동시접속 미지원**: 멀티플레이어 로직 없음

---

## 🔧 마이그레이션 가이드

### v22.0 → v22.1 업그레이드

1. **파일 교체**:
   ```bash
   cp server_patch_v22.1.py server.py
   ```

2. **설정 확인**:
   ```python
   # server.py
   class ServerConfig:
       GAME_IP = "YOUR_PUBLIC_IP"  # 반드시 수정!
   ```

3. **테스트**:
   ```bash
   python server.py
   ```

4. **로그 확인**:
   - `[SUCCESS]` 메시지가 나타나는지 확인
   - 세션 키 검증 로그 확인

---

## 📞 문제 해결

### Q: 클라이언트가 연결 후 바로 끊김
**A**: 엔디안 문제. 모든 `struct.pack`이 `<`를 사용하는지 확인

### Q: 맵 화면이 검은색
**A**: 좌표가 잘못됨. 0x86 패킷의 px, py 값 확인

### Q: "세션 키 불일치" 오류
**A**: 인증 서버와 게임 서버가 `SESSION_STORE`를 공유하는지 확인

### Q: 캐릭터 이름이 깨짐
**A**: EUC-KR 인코딩 문제. `encode_euckr_fixed` 함수 사용

---

**패치 작성자**: AI Assistant  
**패치 날짜**: 2025-10-07  
**라이선스**: 저작권 만료된 게임 복원 프로젝트 전용