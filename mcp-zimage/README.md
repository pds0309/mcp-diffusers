# Z-Image MCP Server

FastMCP와 Diffusers를 사용하여 [Z-Image](https://huggingface.co/Tongyi-MAI/Z-Image) 모델을 서빙하는 MCP 서버입니다. 생성된 이미지는 MinIO에 저장되고 URL로 반환됩니다.


## 주요 기능
- **이미지 생성**: `generate_image` 툴을 통해 텍스트 프롬프트로 이미지를 생성합니다.
- **MinIO 연동**: 생성된 이미지는 자동으로 MinIO 버킷에 업로드됩니다.
- **스트리밍 지원**: Streamable HTTP 프로토콜을 사용하여 안정적인 연결을 지원합니다.
- **백그라운드 실행**: 서버는 백그라운드 프로세스로 실행되며 PID로 관리됩니다.(host 실행 시)


## 요구 사항
- Python 3.10 이상
- Poetry (의존성 관리)
- MinIO 서버 (실행 중일 것)


## 설치 및 실행 방법

### 1. 환경 설정
`env.template` 파일을 참고하여 `.env`를 생성합니다.
```ini
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=zimage
# 선택 사항: 전송 프로토콜 (기본값: streamable-http)
# sse 또는 streamable-http 사용 가능
MCP_TRANSPORT=streamable-http
```

### 2. 의존성 설치
프로젝트 루트에서 다음 명령어로 의존성을 설치합니다. (최초 1회)
```bash
poetry install
```

### 3. 서버 실행
다음 스크립트를 실행하면 가상환경을 활성화하고 서버를 백그라운드에서 시작합니다.
```bash
./_run.sh
```
*주의: 최초 실행 시 대용량 모델을 다운로드하므로 시간이 소요될 수 있습니다. `server.log` 파일을 통해 진행 상황을 확인할 수 있습니다.*

서버는 기본적으로 `http://localhost:8000/sse` 에서 수신 대기합니다. (sse 모드인 경우)

### 4. 서버 중지
실행 중인 서버를 안전하게 종료하려면 다음 스크립트를 실행하세요.
```bash
./_stop.sh
```

## MCP 클라이언트 연동 (Claude Desktop 예시)

`claude_desktop_config.json` 파일을 열고 다음과 같이 서버를 추가하세요. `command` 방식이 아닌 `endpoint` 방식을 사용합니다.

```json
{
  "mcpServers": {
    "z-image": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```
*참고: FastMCP의 Streamable HTTP 엔드포인트는 기본적으로 `/mcp` 경로를 사용합니다.*

*만약 `MCP_TRANSPORT=sse`로 설정한 경우, 엔드포인트는 `/sse`가 됩니다.*