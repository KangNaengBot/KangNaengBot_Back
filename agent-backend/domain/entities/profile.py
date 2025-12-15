"""
Profile Entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Profile:
    """사용자 프로필 엔티티"""
    id: Optional[int]
    user_id: int
    profile_name: str
    student_id: str
    college: str
    department: str
    major: str
    current_grade: int
    current_semester: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @classmethod
    def create(cls, user_id: int, profile_name: str, student_id: str, 
               college: str, department: str, major: str, 
               current_grade: int, current_semester: int) -> 'Profile':
        """새 프로필 생성"""
        return cls(
            id=None,
            user_id=user_id,
            profile_name=profile_name,
            student_id=student_id,
            college=college,
            department=department,
            major=major,
            current_grade=current_grade,
            current_semester=current_semester
        )
