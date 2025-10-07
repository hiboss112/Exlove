# 🔍 타일 렌더링 함수 찾기 가이드

## 현재 상황
- 타일 인덱스가 -2 (0xFFFFFFFE)로 초기화됨 확인
- 타일셋 로딩 함수들은 플래그만 검증, 실제 그리기는 하지 않음
- **실제로 화면에 빨간색을 그리는 렌더링 함수를 찾아야 함**

---

## 🎯 IDA Pro에서 지금 바로 실행할 검색

### 방법 1: Windows GDI 함수 검색 (가장 가능성 높음)

#### 1-1. BitBlt / StretchBlt 검색
```
1. Ctrl + F (Search)
2. "BitBlt" 또는 "StretchBlt" 입력
3. 찾은 함수에서 Ctrl + X (Cross-reference)
4. 호출하는 함수 확인
```

**예상되는 호출 패턴:**
```c
// 타일 렌더링 루프
for (y = 0; y < 19; y++) {
    for (x = 0; x < 25; x++) {
        BitBlt(hdc, x*32, y*32, 32, 32, ...);
    }
}
```

#### 1-2. FillRect / SetPixel 검색
```
1. Ctrl + F → "FillRect"
2. Ctrl + F → "SetPixel"
```

**예상 패턴:**
```c
// 타일 인덱스 -2일 때
if (tile_id == -2 || tile_id == 0xFFFFFFFE) {
    RECT rect = {x*32, y*32, (x+1)*32, (y+1)*32};
    FillRect(hdc, &rect, CreateSolidBrush(RGB(255, 0, 0)));  // 빨간색!
}
```

---

### 방법 2: DirectX 함수 검색

```
Ctrl + F로 검색:
- "DrawPrimitive"
- "DrawIndexedPrimitive"
- "SetTexture"
- "Clear"
- "Present"
```

---

### 방법 3: 빨간색 RGB 값 직접 검색

#### 3-1. 16진수 검색
```
Alt + B (Binary search)
검색: FF 00 00 (빨간색 RGB, Little Endian)
또는: 00 00 FF (Big Endian)
```

#### 3-2. Immediate 값 검색
```
Alt + I (Immediate value)
검색: 0xFF0000 (16711680)
또는: 0x00FF00FF (ARGB 빨간색)
```

#### 3-3. RGB/D3DCOLOR 매크로 검색
```
Alt + T (Text search)
검색: "255, 0, 0"
또는: "0xFF, 0, 0"
또는: "RGB(255"
```

---

### 방법 4: 루프 패턴으로 렌더링 함수 찾기

#### 4-1. 타일 그리드 크기 상수 검색
```
Alt + I (Immediate value)
검색:
- 32 (0x20) - 타일 크기
- 25 (0x19) - 가로 타일 개수 (800 ÷ 32)
- 19 (0x13) - 세로 타일 개수 (600 ÷ 32)
```

#### 4-2. 중첩 루프 식별
IDA Graph View (스페이스바)에서:
- 2중 루프 구조 (네모 블록이 겹침)
- 내부 루프에서 그리기 함수 호출
- 루프 카운터가 25 또는 19

---

### 방법 5: memset32의 Cross-Reference 추적

#### 5-1. -2로 초기화한 배열 사용처 찾기
```
1. sub_401B60 함수로 이동
2. memset32(this + 18, -2, 0x1E) 부분 찾기
3. this + 18 (오프셋 72) 배열을 읽는 곳 검색
   - Ctrl + F → "72" 또는 "[eax+48h]" (72 = 0x48)
```

#### 5-2. 예상 패턴
```c
// 렌더링 함수 어딘가에서
tile_index = this->tile_array[y * width + x];  // this+18 배열 읽기
if (tile_index == -2) {
    // 빨간색 그리기!
}
```

---

### 방법 6: 문자열 검색으로 힌트 찾기

```
Shift + F12 (Strings window)
검색어:
- "tile"
- "map"
- "draw"
- "render"
- "blit"
- "texture"
- "red" (혹시 디버그 메시지가 있을 수도)
```

---

### 방법 7: HDC (Device Context) 사용처 검색

```
1. Alt + T → "GetDC" 또는 "CreateCompatibleDC"
2. 찾은 함수에서 Ctrl + X
3. DC를 사용하는 그리기 함수 추적
```

---

## 🔥 고급 기법: 동적 분석 힌트

### 조건부 브레이크포인트 설정
```
1. OllyDbg 또는 x64dbg로 게임 실행
2. BitBlt 또는 StretchBlt에 BP 설정
3. 빨간색이 나타날 때 호출 스택 확인
4. 해당 주소를 IDA에서 검색
```

### API 모니터링
```
1. API Monitor 사용
2. GDI/GDI+ 함수 필터링
3. RGB(255, 0, 0) 또는 0xFF0000 인자 추적
```

---

## 📊 체크리스트

완료하면 ✓ 표시:

- [ ] BitBlt/StretchBlt 검색
- [ ] FillRect 검색
- [ ] DirectX DrawPrimitive 검색
- [ ] 0xFF0000 (빨간색) 검색
- [ ] RGB(255, 0, 0) 텍스트 검색
- [ ] 타일 크기 32 검색
- [ ] 타일 개수 25, 19 검색
- [ ] memset32의 this+18 배열 사용처 추적
- [ ] GetDC/CreateCompatibleDC 검색
- [ ] Strings 창에서 "tile", "map" 검색

---

## 💡 가능성 높은 시나리오

### 시나리오 A: GDI 기반 렌더링
```c
HDC hdc = GetDC(hwnd);
for (int y = 0; y < 19; y++) {
    for (int x = 0; x < 25; x++) {
        int tile_id = map->tiles[y][x];
        if (tile_id == -2 || tile_id == 0xFFFFFFFE) {
            // 빨간색으로 채우기
            HBRUSH brush = CreateSolidBrush(RGB(255, 0, 0));  // ← 찾아야 할 코드!
            RECT rect = {x*32, y*32, (x+1)*32, (y+1)*32};
            FillRect(hdc, &rect, brush);
            DeleteObject(brush);
        } else {
            // 정상 타일 그리기
            BitBlt(hdc, x*32, y*32, 32, 32, tile_dc, ...);
        }
    }
}
ReleaseDC(hwnd, hdc);
```

### 시나리오 B: DirectX 기반 렌더링
```c
// 타일 인덱스 -2일 때
if (tile_index == -2) {
    D3DCOLOR red = D3DCOLOR_XRGB(255, 0, 0);  // ← 찾아야 할 코드!
    device->Clear(0, NULL, D3DCLEAR_TARGET, red, 1.0f, 0);
}
```

### 시나리오 C: 메모리 직접 조작
```c
// 타일 인덱스 -2일 때
if (tile_index == -2) {
    DWORD* pixels = framebuffer + (y*32*800) + (x*32);
    for (int i = 0; i < 32; i++) {
        for (int j = 0; j < 32; j++) {
            pixels[i*800 + j] = 0x00FF0000;  // ← 찾아야 할 코드!
        }
    }
}
```

---

## 🚀 다음 단계

위의 검색 방법을 **하나씩 시도**해서:
1. 빨간색 상수 (0xFF0000, RGB(255,0,0))를 찾거나
2. 타일 렌더링 루프를 찾으면
3. 해당 코드를 여기에 붙여넣기!

**검색 결과가 너무 많으면, 주변 코드 컨텍스트와 함께 보여주세요.**