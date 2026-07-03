import os
import tempfile
import io
from PIL import Image, ImageDraw, ImageFont
from google.genai import types
from google.adk.tools.tool_context import ToolContext

async def assemble_story_book_pdf(tool_context: ToolContext) -> str:
    """5개의 이미지 아티팩트와 텍스트를 조립하여 최종 complete_story_book.pdf 아티팩트를 생성합니다."""
    # 1. 스토리 작가의 데이터 로드
    story_writer_output = tool_context.state.get("story_writer_output", {})
    if not story_writer_output:
        story_writer_output = tool_context.state.get("story_plan", {})
        
    if not story_writer_output:
        return "❌ 오류: 스토리 작성 데이터를 찾을 수 없습니다."

    pages_data = story_writer_output.get("pages", [])
    if len(pages_data) < 5:
        return f"❌ 오류: 페이지 수가 부족합니다. (현재 {len(pages_data)}개)"

    # 2. 한글 폰트 로드 (윈도우 환경 기본 지정)
    font_path = "C:\\Windows\\Fonts\\malgun.ttf"
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\arial.ttf"
    try:
        font = ImageFont.truetype(font_path, 28)
    except IOError:
        font = ImageFont.load_default()

    page_images = []
    temp_files = []

    try:
        # 3. 각 페이지별로 이미지와 텍스트 합성
        for i in range(1, 6):
            filename = f"page_{i}_image.jpeg"
            page_info = None
            for p in pages_data:
                if int(p.get("page_number", 0)) == i:
                    page_info = p
                    break
            
            if not page_info:
                return f"❌ 오류: {i}페이지 텍스트 정보를 찾을 수 없습니다."

            text_content = page_info.get("text", "")
            
            # 아티팩트 로드
            img_artifact = await tool_context.load_artifact(filename=filename)
            if not img_artifact or not img_artifact.inline_data:
                return f"❌ 오류: 아티팩트 {filename}을 불러올 수 없습니다."

            # 임시 파일 작성
            temp_img = tempfile.NamedTemporaryFile(suffix=".jpeg", delete=False)
            temp_img.write(img_artifact.inline_data.data)
            temp_img.close()
            temp_files.append(temp_img.name)

            # 이미지 로드 및 리사이즈 (정사각형 1024x1024)
            pil_img = Image.open(temp_img.name).convert("RGB")
            pil_img = pil_img.resize((1024, 1024))

            # 합성용 캔버스 생성 (1024x1224: 이미지 1024 + 텍스트 공간 200)
            canvas = Image.new("RGB", (1024, 1224), "white")
            canvas.paste(pil_img, (0, 0))

            # 텍스트 줄바꿈 및 중앙 정렬 그리기
            draw = ImageDraw.Draw(canvas)
            lines = []
            words = text_content.split(" ")
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                left, top, right, bottom = draw.textbbox((0, 0), test_line, font=font)
                if right - left < 920: # 좌우 50픽셀씩 마진 확보
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

            # 텍스트 렌더링 (y=1050부터 시작)
            text_y = 1050
            for line in lines:
                left, top, right, bottom = draw.textbbox((0, 0), line, font=font)
                text_x = (1024 - (right - left)) // 2
                draw.text((text_x, text_y), line, fill="black", font=font)
                text_y += (bottom - top) + 10

            page_images.append(canvas)

        if not page_images:
            return "❌ 오류: 조립된 이미지가 존재하지 않습니다."

        # 4. 다중 페이지 PDF 변합
        pdf_bytes = io.BytesIO()
        first_img = page_images[0]
        first_img.save(
            pdf_bytes,
            format="PDF",
            save_all=True,
            append_images=page_images[1:],
            resolution=100.0,
            quality=90
        )
        pdf_data = pdf_bytes.getvalue()

        # 5. 아티팩트 저장
        artifact = types.Part(
            inline_data=types.Blob(mime_type="application/pdf", data=pdf_data)
        )

        await tool_context.save_artifact(
            filename="complete_story_book.pdf",
            artifact=artifact
        )

        return "PDF 동화책 어셈블 완료"

    finally:
        # 임시 파일 삭제
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except Exception:
                pass
