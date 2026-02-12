from __future__ import annotations

import os
import io
import time
import asyncio
import logging
from typing import Annotated, Optional

from dotenv import load_dotenv

from fastmcp import FastMCP, Context
from pydantic import Field

from inference import ZImagePipeline
from storage import Storage

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing Z-Image Pipeline...")
pipeline = ZImagePipeline()
logger.info("Initializing Storage...")
storage = Storage()

mcp = FastMCP("Z-Image Generator")


def _generate_and_upload_sync(
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        num_inference_steps: int,
        guidance_scale: float,
        seed: int,
) -> str:
    """오래 걸리는 동기 작업 (모델 추론 + 업로드). executor로 실행."""
    image = pipeline.generate(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        seed=seed,
    )

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    url = storage.upload_image(buf.getvalue(), ext="png")
    return url


@mcp.tool()
async def generate_image(
        prompt: Annotated[str, Field(
            description="이미지 생성 프롬프트. [주제/피사체] => [동작/상황] => [스타일/아티스트/장르] => [구도/카메라/렌즈] => [조명/분위기] => [디테일/품질 키워드] 순으로 영문 자연어로 자세히 작성",
            min_length=1,
            examples=[
                "A beautiful girl with long silver hair, standing in a snowy forest, anime style, Makoto Shinkai style, cinematic lighting, volumetric light, 85mm lens, shallow depth of field, ultra detailed, masterpiece, 8k"]
        )],
        negative_prompt: Annotated[str, Field(
            description="피하고 싶은 요소들. 쉼표로 나열",
            examples=["low quality, blurry, extra fingers"]
        )] = "low quality, worst quality, blurry, low resolution, jpeg artifacts, distorted, deformed, bad anatomy, bad proportions, extra fingers, malformed hands",
        width: Annotated[int, Field(
            description="출력 이미지 너비(px). 16의 배수 권장",
            ge=256, le=1920, examples=[360, 480, 720, 1024, 1280, 1920]
        )] = 720,
        height: Annotated[int, Field(
            description="출력 이미지 높이(px). 16의 배수 권장",
            ge=256, le=1280, examples=[360, 480, 720, 1024, 1280]
        )] = 720,
        num_inference_steps: Annotated[int, Field(
            description="디노이징 스텝 수. 높을수록 품질↑/속도↓ (권장 20~50)",
            ge=10, le=50, examples=[30]
        )] = 30,
        guidance_scale: Annotated[float, Field(
            description="프롬프트 반영 강도(CFG). 높을수록 프롬프트에 충실, 과하면 부자연 (권장 3~6)",
            ge=1, le=10, examples=[4, 5.5]
        )] = 4,
        seed: Annotated[int, Field(
            description="난수 시드. -1이면 매번 랜덤",
            ge=-1, le=2_147_483_647, examples=[-1, 42]
        )] = -1,
        ctx: Optional[Context] = None,
) -> str:
    """
    Generate an image using Z-Image model and return the public URL.

    서버가 중간중간 ctx.info / ctx.report_progress 를 보내서
    Langflow/IDE 쪽 idle(read) timeout을 완화하는 버전.
    """
    logger.info(f"Received request: {prompt}")

    # 중간 메시지 전송 주기(초)
    heartbeat_s = float(os.getenv("MCP_HEARTBEAT_S", "5"))
    # 강제로 SSE 스트림을 주기적으로 끊었다가 재연결하게 하는 옵션(프록시/LB가 오래된 연결을 끊는 환경 대응)
    enable_close_sse = os.getenv("MCP_CLOSE_SSE_STREAM", "0") == "1"
    close_sse_every = int(os.getenv("MCP_CLOSE_SSE_EVERY", "30"))  # progress 카운트 기준

    started = time.time()

    if ctx is not None:
        # ctx.info / ctx.report_progress는 클라이언트에 실시간으로 전달됨(클라이언트가 지원하는 경우)
        # FastMCP Context 사용 패턴 :contentReference[oaicite:1]{index=1}
        await ctx.info("✅ generate_image started")
        await ctx.info(f"prompt={prompt[:120]}")
        # 진행률은 “시간 기반”으로라도 계속 갱신해서 idle 구간을 없애는 목적
        await ctx.report_progress(0, 100)

    loop = asyncio.get_running_loop()

    # 동기 작업을 executor로 돌림(이렇게 해야 event loop가 살아있어서 중간 이벤트를 보낼 수 있음)
    task = loop.run_in_executor(
        None,
        _generate_and_upload_sync,
        prompt,
        negative_prompt,
        width,
        height,
        num_inference_steps,
        guidance_scale,
        seed,
    )

    tick = 0
    # 완료될 때까지 주기적으로 progress/log 전송
    while True:
        done, _ = await asyncio.wait({task}, timeout=heartbeat_s)
        if done:
            break

        tick += 1
        elapsed = int(time.time() - started)

        if ctx is not None:
            # “진짜 퍼센트”가 아니라도, 주기적 이벤트가 핵심(무응답 구간 제거)
            # 0~99 범위로만 돌게 해서 UX도 맞춤
            pseudo_progress = min(99, tick % 100)
            await ctx.report_progress(pseudo_progress, 100)
            await ctx.info("\n")
            await ctx.info(f"⏳ still working... elapsed={elapsed}s")

            # (옵션) 일부 LB/프록시가 장시간 SSE 연결을 끊는 경우,
            # FastMCP가 지원하면 주기적으로 스트림을 닫아 클라이언트가 재연결/재개하게 할 수 있음 :contentReference[oaicite:2]{index=2}
            if enable_close_sse and tick % close_sse_every == 0:
                close_fn = getattr(ctx, "close_sse_stream", None)
                if callable(close_fn):
                    await close_fn()

    url = await task

    logger.info(f"Image uploaded to: {url}")

    if ctx is not None:
        await ctx.report_progress(100, 100)
        await ctx.info(f"✅ done. url={url}")

    return url


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport, port=8000, host="0.0.0.0")
