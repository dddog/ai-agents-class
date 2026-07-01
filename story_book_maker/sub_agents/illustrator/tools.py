import base64
import os
import tempfile
from openai import OpenAI
from google.genai import types
from google.adk.tools.tool_context import ToolContext
from PIL import Image, ImageDraw, ImageFont

client = OpenAI()


async def generate_illustrations(tool_context: ToolContext):
    """지정된 페이지의 일러스트를 gpt-image-1 모델을 사용해 1:1 정사각형 비율로 생성합니다."""
    story_writer_output = tool_context.state.get("story_writer_output", {})
    if not story_writer_output:
        return "스토리 작가의 결과 데이터가 상태(State)에 존재하지 않습니다."

    page_number = story_writer_output.get("page_number")
    text = story_writer_output.get("text")
    visual_description = story_writer_output.get("visual_description")
    character_description = story_writer_output.get("character_description")

    filename = f"page_{page_number}_image.jpeg"

    # 캐싱 확인 (이미 존재하면 다시 생성 안 함)
    existing_artifacts = await tool_context.list_artifacts()
    if filename in existing_artifacts:
        # 이미지가 존재할 경우 데이터 누적만 수행
        pages_data = tool_context.state.get("pages_data", {})
        pages_data[str(page_number)] = {"text": text, "image_file": filename}
        tool_context.state["pages_data"] = pages_data
        return f"이미 {page_number}페이지의 이미지가 아티팩트로 저장되어 있습니다."

    # 짱구는 못말려 스타일 적용 및 캐릭터 일관성 프롬프트 조립
    style_prompt = "짱구는 못말려 애니메이션 스타일, 굵은 아웃라인, 단순한 단색 채색, 귀여운 아동 동화책 일러스트, Crayon Shin-chan animation style, bold outlines, simple colors, flat shading, children's book illustration"
    final_prompt = (
        f"{visual_description}. "
        f"캐릭터 상세 특징(동화 전체 고정): {character_description}. "
        f"그림 화풍 규격: {style_prompt}."
    )

    print(
        f"🎨 ILLUSTRATOR: {page_number}페이지 이미지 생성 요청 (모델: gpt-image-1)"
    )

    image = client.images.generate(
        model="gpt-image-1",
        prompt=final_prompt,
        n=1,
        quality="low",
        moderation="low",
        output_format="jpeg",
        background="opaque",
        size="1024x1024",  # 정사각형 1:1 비율
    )

    image_bytes = base64.b64decode(image.data[0].b64_json)

    artifact = types.Part(
        inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes)
    )

    # 아티팩트 저장
    await tool_context.save_artifact(
        filename=filename,
        artifact=artifact,
    )

    # UI 렌더링용 base64 캐싱 (에이전트의 after_model_callback에서 가져감)
    tool_context.state["last_image_base64"] = image.data[0].b64_json

    # State에 현재 페이지 정보를 저장하여 누적 관리
    pages_data = tool_context.state.get("pages_data", {})
    pages_data[str(page_number)] = {"text": text, "image_file": filename}
    tool_context.state["pages_data"] = pages_data

    return f"{page_number}페이지 일러스트 생성 완료 (파일: {filename})"


async def combine_story_book(tool_context: ToolContext):
    """5페이지의 동화 이미지 아래에 동화 텍스트를 여유 여백을 주어 배치하고 세로로 길게 연결한 단일 병합 파일을 생성합니다."""
    pages_data = tool_context.state.get("pages_data", {})
    if not pages_data or len(pages_data) < 5:
        return f"병합 불가: 최소 5개의 완성된 페이지 정보가 필요합니다. (현재 개수: {len(pages_data)})"

    page_blocks = []
    temp_files = []

    # 폰트 로드 (윈도우 한글 맑은 고딕 기본 지정)
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        # 폰트 없을 시 기본 폰트로 폴백
        font_path = "C:\\Windows\\Fonts\\arial.ttf"

    try:
        font = ImageFont.truetype(font_path, 28)
    except IOError:
        font = ImageFont.load_default()

    max_width = 1024

    for i in range(1, 6):
        page_info = pages_data.get(str(i))
        if not page_info:
            return f"{i}페이지에 대한 정보가 누락되어 병합할 수 없습니다."

        img_filename = page_info["image_file"]
        text_content = page_info["text"]

        img_artifact = await tool_context.load_artifact(filename=img_filename)
        if not img_artifact or not img_artifact.inline_data:
            return f"{img_filename} 아티팩트를 불러오는 데 실패했습니다."

        # 임시 파일로 쓰기
        temp_img = tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False)
        temp_img.write(img_artifact.inline_data.data)
        temp_img.close()
        temp_files.append(temp_img.name)

        pil_img = Image.open(temp_img.name)
        pil_img = pil_img.resize((1024, 1024))  # 1024x1024 균일화

        page_blocks.append((pil_img, text_content))

    # 여백 정보
    vertical_gap = 30  # 이미지와 텍스트 사이 마진
    text_height_alloc = 120  # 각 페이지당 텍스트 렌더링 세로 높이
    block_gap = 50  # 페이지 블록들 간의 세로 구분 공백

    # 전체 세로 캔버스 크기 계산
    # (이미지 1024 + 여백 30 + 텍스트영역 120 + 블록구분공백 50) * 5
    block_height = 1024 + vertical_gap + text_height_alloc + block_gap
    total_height = block_height * 5

    combined_img = Image.new("RGB", (max_width, total_height), "white")
    draw = ImageDraw.Draw(combined_img)

    current_y = 0
    for i, (img, text_content) in enumerate(page_blocks):
        # 1. 이미지 붙이기
        combined_img.paste(img, (0, current_y))
        current_y += 1024 + vertical_gap

        # 2. 텍스트 줄바꿈 연산 및 중앙 정렬 그리기
        lines = []
        words = text_content.split(" ")
        current_line = ""
        for word in words:
            test_line = current_line + " " + word if current_line else word
            left, top, right, bottom = draw.textbbox((0, 0), test_line, font=font)
            if right - left < 920:  # 좌우 여백 확보
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        text_y = current_y
        for line in lines:
            left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
            text_x = (max_width - (right - left)) // 2
            draw.text((text_x, text_y), line, fill="black", font=font)
            text_y += (bottom - top) + 10

        current_y += text_height_alloc + block_gap

    # 임시 파일 삭제
    for temp_path in temp_files:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except Exception:
            pass

    # 결과물 바이트 변환 후 아티팩트 저장
    import io

    output_bytes = io.BytesIO()
    combined_img.save(output_bytes, format="PNG")
    output_data = output_bytes.getvalue()

    artifact = types.Part(
        inline_data=types.Blob(mime_type="image/png", data=output_data)
    )

    await tool_context.save_artifact(
        filename="story_book_final.png",
        artifact=artifact,
    )

    # UI 노출을 위해 base64로 캐싱
    final_base64 = base64.b64encode(output_data).decode("utf-8")
    tool_context.state["final_image_base64"] = final_base64

    return "최종 동화책 병합 이미지(story_book_final.png) 생성 완료!"
