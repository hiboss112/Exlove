# 🚨 중요 발견: Import 테이블 분석 결과

## ✅ 확인된 그래픽 API

### DirectDraw (DDRAW.dll)
```
DirectDrawCreateEx - DirectDraw 초기화
```
**→ 이 게임은 DirectDraw를 사용합니다!**

### GDI32.dll
```
SetBkColor         - 배경색 설정
SetTextColor       - 텍스트 색상
DeleteObject       - 오브젝트 삭제
DeleteDC           - DC 삭제
CreateDIBSection   - DIB 비트맵 생성
GetTextExtentPoint32A - 텍스트 크기
SelectObject       - 오브젝트 선택
CreateCompatibleDC - 호환 DC 생성
CreateFontA        - 폰트 생성
TextOutA           - 텍스트 출력
PatBlt             - 패턴 블릿 (단색 채우기!)
SetBkMode          - 배경 모드
GetStockObject     - 스톡 오브젝트
```

### ⚠️ 중요: 없는 함수들
```
❌ BitBlt          - 비트맵 복사 (없음!)
❌ StretchBlt      - 비트맵 확대/축소 (없음!)
❌ FillRect        - 사각형 채우기 (없음!)
❌ DrawPrimitive   - DirectX 그리기 (없음!)
```

---

## 🎯 빨간색 렌더링 가능성 분석

### 가능성 1: PatBlt로 단색 채우기 ⭐⭐⭐⭐⭐
```c
// PatBlt는 단색 패턴을 채우는 함수
HDC hdc = GetDC(hwnd);
HBRUSH red_brush = CreateSolidBrush(RGB(255, 0, 0));
SelectObject(hdc, red_brush);
PatBlt(hdc, x, y, 32, 32, PATCOPY);  // ← 빨간색 타일!
DeleteObject(red_brush);
ReleaseDC(hwnd, hdc);
```
**확률: 95%** - 가장 가능성 높음!

### 가능성 2: DirectDraw Surface 직접 조작 ⭐⭐⭐
```c
// DirectDraw Surface Lock
DDSURFACEDESC2 ddsd;
lpDDSurface->Lock(NULL, &ddsd, DDLOCK_WAIT, NULL);

// 픽셀 직접 쓰기
DWORD* pixels = (DWORD*)ddsd.lpSurface;
for (int i = 0; i < 32*32; i++) {
    pixels[i] = 0x00FF0000;  // 빨간색!
}

lpDDSurface->Unlock(NULL);
```
**확률: 70%**

### 가능성 3: CreateDIBSection 비트맵 조작 ⭐⭐
```c
// DIB 비트맵 생성
HBITMAP hBitmap = CreateDIBSection(hdc, &bmi, DIB_RGB_COLORS, &pixels, NULL, 0);

// 메모리에 직접 빨간색 쓰기
DWORD* p = (DWORD*)pixels;
for (int i = 0; i < 32*32; i++) {
    p[i] = 0x00FF0000;
}
```
**확률: 50%**

---

## 🔍 IDA Pro에서 지금 바로 검색할 것

### 🥇 최우선 1: PatBlt 검색
```
1. Ctrl + F
2. "PatBlt" 입력
3. 찾으면 Ctrl + X (Cross-reference)
4. 호출하는 함수를 F5로 디컴파일
```

**예상 코드:**
```c
void DrawTile(int x, int y, int tile_index) {
    if (tile_index == -2) {
        HBRUSH brush = CreateSolidBrush(RGB(255, 0, 0));  // 빨간색!
        SelectObject(hdc, brush);
        PatBlt(hdc, x*32, y*32, 32, 32, PATCOPY);
        DeleteObject(brush);
    }
}
```

---

### 🥈 최우선 2: CreateSolidBrush + RGB 매크로
**RGB 매크로 정의:**
```c
#define RGB(r,g,b) ((COLORREF)(((BYTE)(r)|((WORD)((BYTE)(g))<<8))|(((DWORD)(BYTE)(b))<<16)))
RGB(255, 0, 0) = 0x000000FF  // Little Endian에서는 이렇게 저장됨
```

**IDA에서 검색:**
```
Alt + I (Immediate value)
검색: 255 (0xFF) - 빨간색 R 값
```

**또는:**
```
Alt + T (Text search)
검색: "255" - 주변에 0, 0이 있는지 확인
```

---

### 🥉 최우선 3: DirectDraw Lock 검색
```
Ctrl + F
"Lock" 또는 "lpSurface" 검색
```

**예상 코드:**
```c
lpDDSurface->Lock(NULL, &ddsd, DDLOCK_WAIT, NULL);
DWORD* pixels = (DWORD*)ddsd.lpSurface;
// 타일 인덱스 -2일 때
if (tile_index == -2) {
    int offset = (y * 800) + x;
    for (int i = 0; i < 32; i++) {
        for (int j = 0; j < 32; j++) {
            pixels[offset + i*800 + j] = 0x00FF0000;  // 빨간색!
        }
    }
}
lpDDSurface->Unlock(NULL);
```

---

### 4️⃣ CreateDIBSection 검색
```
Ctrl + F
"CreateDIBSection"
```

---

### 5️⃣ SelectObject 검색 (브러시 선택)
```
Ctrl + F
"SelectObject"
→ 주변에 CreateSolidBrush가 있는지 확인
```

---

## 📊 검색 우선순위 요약

| 순위 | 함수 | 확률 | 검색 방법 |
|------|------|------|-----------|
| 🥇 | **PatBlt** | 95% | Ctrl+F → "PatBlt" |
| 🥈 | **RGB(255,0,0)** | 90% | Alt+I → "255" |
| 🥉 | **DirectDraw Lock** | 70% | Ctrl+F → "Lock" |
| 4 | CreateDIBSection | 50% | Ctrl+F → "CreateDIBSection" |
| 5 | SelectObject | 80% | Ctrl+F → "SelectObject" |

---

## 💡 실전 검색 순서

### Step 1: PatBlt 찾기
```
IDA Pro에서:
1. Ctrl + F
2. "PatBlt" 입력
3. 함수 주소 확인 (00481060 근처일 것)
4. 해당 주소에서 Ctrl + X (xref)
5. 호출하는 함수 디컴파일 (F5)
```

### Step 2: SelectObject 역추적
```
1. Ctrl + F → "SelectObject"
2. Ctrl + X로 호출 함수 확인
3. CreateSolidBrush와 함께 사용되는지 확인
4. RGB 값 255, 0, 0 찾기
```

### Step 3: 0xFF 상수 검색
```
Alt + I (Immediate search)
255 검색
→ 주변 코드에서 0, 0이 연속으로 있는지 확인
→ RGB(255, 0, 0) 패턴
```

---

## 🎯 다음 액션

**지금 IDA Pro에서 실행하세요:**

```
1. Ctrl + F
2. "PatBlt" 입력
3. 찾은 Import 주소 (0048105C)로 이동
4. Ctrl + X (Cross-reference to)
5. 호출하는 함수를 F5로 디컴파일
6. 전체 코드 복사해서 보여주기!
```

**이 함수가 90% 확률로 빨간색 타일을 그리는 코드입니다!** 🔥

---

## 🔬 추가 힌트

### GDI 단색 채우기 패턴
```c
// 전형적인 GDI 단색 채우기 코드
HBRUSH hBrush = CreateSolidBrush(RGB(r, g, b));
HBRUSH hOldBrush = (HBRUSH)SelectObject(hdc, hBrush);
PatBlt(hdc, x, y, width, height, PATCOPY);
SelectObject(hdc, hOldBrush);
DeleteObject(hBrush);
```

### PATCOPY 상수
```
PATCOPY = 0x00F00021
→ IDA에서 이 상수도 검색해볼 것
```

---

**PatBlt를 사용하는 함수를 찾으면 거의 확실히 문제를 해결할 수 있습니다!**