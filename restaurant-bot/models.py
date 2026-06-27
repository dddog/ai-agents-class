from pydantic import BaseModel
from typing import Optional

# 사용자 계정 맥락 정보를 담는 Pydantic 모델
class UserAccountContext(BaseModel):
    customer_id: int  # 고객 식별 ID
    name: str  # 고객 이름
    tier: str = "basic"  # 고객 등급 (기본값: basic)
    email: Optional[str] = None  # 프리미엄/엔터프라이즈 등급일 경우의 이메일 주소


# 입력 가드레일 판정 결과를 정의하는 모델
class InputGuardRailOutput(BaseModel):
    is_off_topic: bool  # 사용자의 입력이 지원 범위를 벗어났는지(off-topic) 여부
    reason: str  # 오프토픽 판정 사유 혹은 트립와이어(tripwire) 트리거 이유


# 기술 지원 에이전트의 출력 검증 가드레일 모델
class TechnicalOutputGuardRailOutput(BaseModel):
    contains_off_topic: bool  # 기술 범위를 벗어난 주제 포함 여부
    contains_billing_data: bool  # 청구/결제 관련 정보가 기술 지원 응답에 포함되어 있는지 여부
    contains_account_data: bool  # 계정 관리 관련 정보가 기술 지원 응답에 포함되어 있는지 여부
    reason: str  # 가드레일 판정 결과에 대한 상세 사유


# 에이전트 간 업무 전환(Handoff) 발생 시 전송할 정보 모델
class HandoffData(BaseModel):
    to_agent_name: str  # 인계받을 에이전트의 이름
    issue_type: str  # 이슈의 분류 카테고리
    issue_description: str  # 이슈 설명
    reason: str  # 특정 에이전트로 작업을 인계하는 사유