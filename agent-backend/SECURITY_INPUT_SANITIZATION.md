# 🛡️ 입력 살균 (Input Sanitization) 시스템

## 개요

모든 사용자 입력에 대해 **다층 방어 전략**을 적용하여 XSS, Script Injection, SQL Injection 등의 공격으로부터 시스템을 보호합니다.

## 🔐 방어 계층

### 1️⃣ **Pydantic 모델 검증** (라우터 레벨)
- **위치**: `routers/` 디렉토리
- **역할**: 타입 검증, 길이 제한, 형식 검증
- **예시**:
  ```python
  class MessageRequest(BaseModel):
      message: str
      
      @classmethod
      def validate_message(cls, v: str) -> str:
          if len(v) > 10000:
              raise ValueError("Message is too long")
          return v
  ```

### 2️⃣ **입력 살균** (서비스 레벨) ⭐ **최우선**
- **위치**: `services/` 디렉토리
- **역할**: HTML/Script 제거, 위험 패턴 탐지
- **예시**:
  ```python
  def stream_message(self, message_text: str):
      # 🛡️ 보안: 입력 살균 (최우선 처리)
      message_text = sanitize_message(message_text)
      # ... 비즈니스 로직
  ```

### 3️⃣ **SQL Injection 방어** (ORM 레벨)
- **위치**: SQLAlchemy (자동)
- **역할**: 쿼리 파라미터화, prepared statements
- **방법**: ORM 사용으로 자동 방어

---

## 🛠️ 사용 방법

### 입력 살균 유틸리티

`utils/input_sanitizer.py`에 정의된 함수들을 사용합니다.

#### 1. **채팅 메시지 살균**
```python
from utils.input_sanitizer import sanitize_message

# 최대 5000자, HTML 제거, 줄바꿈 허용
clean_message = sanitize_message(user_message)
```

#### 2. **제목/타이틀 살균**
```python
from utils.input_sanitizer import sanitize_title

# 최대 200자, HTML 제거, 줄바꿈 불허
clean_title = sanitize_title(session_title)
```

#### 3. **사용자 정보 살균**
```python
from utils.input_sanitizer import sanitize_user_info

# 최대 100자, HTML 제거, 줄바꿈 불허
clean_name = sanitize_user_info(profile_name)
clean_student_id = sanitize_user_info(student_id)
```

---

## 🚨 위험 패턴 탐지

### 제거되는 패턴
- `<script>` 태그
- `<iframe>` 태그
- `javascript:` 프로토콜
- `onclick`, `onload` 등 이벤트 핸들러
- `<object>`, `<embed>`, `<applet>` 태그
- `data:text/html` URI

### 경고되는 패턴 (SQL Injection)
- `OR 1=1`, `AND 1=1`
- `DROP`, `DELETE`, `INSERT`, `UPDATE`
- `--` (SQL 주석)
- `UNION SELECT`

**주의**: SQL Injection은 ORM(SQLAlchemy)이 자동으로 방어하므로 경고만 출력됩니다.

---

## 📋 적용 현황

### ✅ 적용 완료

| 엔드포인트 | 입력 필드 | 검증 레벨 | 살균 레벨 |
|-----------|----------|-----------|-----------|
| `POST /chat/message` | `message` | Pydantic (길이) | ChatService (최우선) |
| `POST /profiles` | `profile_name` | Pydantic (max_length=100) | ProfileService (최우선) |
| `POST /profiles` | `student_id` | Pydantic (max_length=20) | ProfileService (최우선) |
| `POST /profiles` | `college` | Pydantic (max_length=100) | ProfileService (최우선) |
| `POST /profiles` | `department` | Pydantic (max_length=100) | ProfileService (최우선) |
| `POST /profiles` | `major` | Pydantic (max_length=100) | ProfileService (최우선) |

---

## 🔍 예시: 공격 차단

### XSS 공격 차단
```python
# 입력
message = "안녕하세요 <script>alert('XSS')</script>"

# 살균 후
clean_message = "안녕하세요 "  # <script> 태그 제거됨
```

### HTML Injection 차단
```python
# 입력
name = "<img src=x onerror=alert(1)>"

# 살균 후
clean_name = "&lt;img src=x onerror=alert(1)&gt;"  # HTML 이스케이핑
```

### 길이 제한
```python
# 입력
message = "A" * 20000  # 20,000자

# 살균 후
clean_message = "A" * 10000  # 10,000자로 잘림
```

---

## 🎯 새로운 엔드포인트 추가 시

새로운 API 엔드포인트를 추가할 때는 다음을 따라주세요:

### 1. Pydantic 모델에 검증 추가
```python
class NewRequest(BaseModel):
    field_name: str = Field(..., max_length=100)
    
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v
```

### 2. 서비스 레이어에 살균 추가
```python
def process_data(self, field_name: str):
    # 🛡️ 보안: 입력 살균 (최우선 처리)
    field_name = sanitize_user_info(field_name)  # 또는 적절한 살균 함수
    
    # ... 비즈니스 로직
```

---

## 📝 로그 확인

입력 살균이 작동하면 다음과 같은 로그가 출력됩니다:

```
[ChatService] ✅ Input sanitized (length: 150)
[ProfileService] ✅ Profile inputs sanitized for user_id=123
[Sanitizer] ⚠️ Dangerous pattern detected: <script[^>]*>.*?</script>
[Sanitizer] Input sanitized: 200 -> 150 chars
```

---

## 🚀 추가 보안 권장사항

### 이미 적용된 것들
- ✅ Rate Limiting (SlowAPI - 1분당 30개 요청)
- ✅ 입력 길이 제한
- ✅ HTML/Script 태그 제거
- ✅ SQL Injection 방어 (ORM)

### 추가로 고려할 것들
- 🔄 CSRF 토큰 (현재 JWT 사용 중)
- 🔄 IP 기반 블랙리스트
- 🔄 비정상 패턴 탐지
- 🔄 로그 모니터링 및 알림

---

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/)
