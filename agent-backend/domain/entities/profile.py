"""
Profile Entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

@dataclass
class Profile:
    """
    사용자 프로필 엔티티

    Attributes:
        id: DB 내부 ID (BIGINT)
        user_id: 사용자 ID
        user_sid: 사용자 외부 노출용 UUID (users.sid) - 응답용
        profile_name: 프로필 이름
        student_id: 학번
        college: 단과대학
        department: 학부/학과
        major: 전공
        current_grade: 현재 학년
        current_semester: 현재 학기
        created_at: 생성 시각
        updated_at: 수정 시각
        deleted_at: 삭제 시각 (Soft Delete)
    """
    id: Optional[int] = None
    user_id: int = 0
    user_sid: Optional[UUID] = None
    profile_name: str = ""
    student_id: str = ""
    college: str = ""
    department: str = ""
    major: str = ""
    current_grade: int = 0
    current_semester: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @classmethod
    def create(cls, user_id: int, profile_name: str, student_id: str,
               college: str, department: str, major: str,
               current_grade: int, current_semester: int) -> 'Profile':
        """새 프로필 생성 (팩토리 메서드)"""
        return cls(
            id=None,
            user_id=user_id,
            user_sid=None,  # Repository에서 조회 후 추가
            profile_name=profile_name,
            student_id=student_id,
            college=college,
            department=department,
            major=major,
            current_grade=current_grade,
            current_semester=current_semester
        )
