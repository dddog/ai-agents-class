import base64
from openai import OpenAI
from google.genai import types
from google.adk.tools.tool_context import ToolContext

client = OpenAI()

async def generate_page_illustration(tool_context: ToolContext, page_number: int) -> str:
    """gpt-image-1 모델을 사용하여 지정된 페이지 번호에 대한 일러스트를 생성하고 저장합니다.

    Args:
        tool_context: 툴 실행 컨텍스트
        page_number: 생성할 동화책의 페이지 번호 (1부터 5까지)
    """
    # 1. 이전 단계에서 저장된 스토리 기획 정보 읽기
    story_writer_output = tool_context.state.get("story_writer_output", {})
    if not story_writer_output:
        story_writer_output = tool_context.state.get("story_plan", {})
        
    if not story_writer_output:
        return f"❌ 오류: 스토리 작성 데이터를 찾을 수 없습니다."

    characters_description = story_writer_output.get("characters_description", "")
    pages = story_writer_output.get("pages", [])
    
    # 2. 현재 페이지에 맞는 스토리 요소 찾기
    page_data = None
    for p in pages:
        if int(p.get("page_number", 0)) == page_number:
            page_data = p
            break
            
    if not page_data:
        return f"❌ 오류: {page_number}페이지 정보를 찾을 수 없습니다."
        
    visual_description = page_data.get("visual_description", "")
    composition_description = page_data.get("composition_description", "")  # 구도 정보가 있다면 추가 추출 (선택사항)
    filename = f"page_{page_number}_image.jpeg"
    
    # 3. 중복 생성 방지 캐싱
    existing_artifacts = await tool_context.list_artifacts()
    if filename in existing_artifacts:
        return f"page_{page_number}_image.jpeg 이미 존재하여 생성 스킵."

    # 4. 프롬프트 조합 (에이전트 고정형 시스템 구조 적용)
    system_instruction = (
        "[역할 정의]\n"
        "당신은 일관된 화풍과 캐릭터를 고정하여 동화책 일러스트를 생성하는 전문 AI 아티스트입니다. "
        "제공된 [스타일 가이드]와 [캐릭터 정의]를 모든 페이지에 엄격하고 동일하게 적용해야 합니다.\n\n"
    )
    
    style_guide = (
        "[스타일 가이드 (STYLE)]\n"
        "- 그림체: 짱구는 못말려 애니메이션 스타일 (Crayon Shin-chan animation style), 굵고 명확한 아웃라인 (Bold outlines), 평면적인 채색 및 음영 (Flat shading)\n"
        "- 색상 조합: 단순하고 선명한 단색 채색 (Simple colors)\n"
        "- 분위기: 귀여운 아동 동화책 일러스트 (Cute children's book illustration)\n"
        "- 제외 항목 (Negative): 사진 같은 실사(Realism), 3D 렌더링, 어두운 그림자, 복잡한 그라데이션, 네온 컬러\n\n"
    )
    
    character_definition = (
        f"[캐릭터 정의 (CHARACTER)]\n"
        f"{characters_description}\n\n"
    )
    
    current_scene = (
        f"[현재 페이지]: Page {page_number}\n"
        f"[장면 묘사]: {visual_description}\n"
        f"[구도 및 연출]: {composition_description if composition_description else '중앙 중심 구도'}\n\n"
        f"**주의**: 이전 페이지와 연계된 캐릭터 특성 및 지정된 화풍의 일관성을 완벽하게 유지하십시오."
    )
    
    final_prompt = f"{system_instruction}{style_guide}{character_definition}{current_scene}"
    
    # print(f"🎨 [Illustrator Page {page_number}] 이미지 생성 요청 중 (모델: gpt-image-1)")
    
    # 5. gpt-image-1 모델 API 호출
    image = client.images.generate(
        model="gpt-image-1",
        prompt=final_prompt,
        n=1,
        quality="low",
        moderation="low",
        output_format="jpeg",
        background="opaque",
        size="1024x1024",
    )
    
    image_bytes = base64.b64decode(image.data[0].b64_json)
    
    artifact = types.Part(
        inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes)
    )
    
    # 6. 아티팩트 저장
    await tool_context.save_artifact(
        filename=filename,
        artifact=artifact,
    )
    
    return f"page_{page_number}_image.jpeg 생성 완료"