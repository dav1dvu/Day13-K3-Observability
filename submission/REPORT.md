# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`:
- Tổng số traces: 14 traces (tag `lab`) trên Langfuse, vượt mức tối thiểu 10. 10 trace từ `data/sample_queries.jsonl` (load test) + 2 trace so sánh baseline/candidate + 2 trace demo đổi/rollback label `production`.
- Số PII leak còn lại:
- Link/đường dẫn dashboard: `https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4`

## 3. Logging và tracing

- Evidence correlation ID:
- Evidence PII redaction:
- Evidence trace waterfall: trace `f3ec5ed102f47370096f5b5254d49ba7` — https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4/traces/f3ec5ed102f47370096f5b5254d49ba7
  - `run` (GENERATION, root span, 1.06s) chứa hai con: `retrieve` (SPAN) và `generate` (GENERATION), cả hai đều có `parent_observation_id` trỏ về `run`, tạo cấu trúc waterfall tách rõ thời gian RAG vs LLM.
  - Ảnh cần chụp: `submission/evidence/trace-waterfall.png`
- Giải thích một span đáng chú ý: Span `retrieve` (từ `@observe()` trong [app/mock_rag.py](../app/mock_rag.py)) chạy gần như tức thời (tra cứu dict trong bộ nhớ) và ghi metadata `matched_key`/`doc_count`, cho thấy request khớp corpus nào. Span con `generate` (từ `@observe(as_type="generation")` trong [app/mock_llm.py](../app/mock_llm.py)) chiếm phần lớn latency (~150ms sleep giả lập LLM) và được Langfuse coi là generation riêng — tách bạch chi phí/độ trễ LLM khỏi bước truy xuất tài liệu.

## 4. Prompt versioning

- Prompt name: `day13-chat` (text prompt, 3 biến `feature`/`docs`/`message`)
- Version/label baseline: version 1, labels `baseline` + `production` (khi tạo)
- Version/label candidate: version 2, label `candidate` — thêm ràng buộc "Answer in at most 3 concise sentences using only the provided Docs." so với v1
- Trace ID của mỗi version:
  - label=`baseline` → version 1 → trace `36879d11eac7f484b40bca10968e6e43` — https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4/traces/36879d11eac7f484b40bca10968e6e43
  - label=`candidate` → version 2 → trace `884c5af5883c81820e312a5a314c89f6` — https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4/traces/884c5af5883c81820e312a5a314c89f6
  - Ảnh cần chụp: `submission/evidence/prompt-versions-list.png` (danh sách 2 version trên Langfuse)
- Bằng chứng đổi label hoặc rollback:
  - Đổi `production`: v1 → v2 qua `client.update_prompt(name="day13-chat", version=2, new_labels=["candidate", "production"])`. Request sau đó dùng label mặc định `production` và resolve đúng version 2 → trace `c991bc442a2efbc9bfc18c41f5ee2b67` — https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4/traces/c991bc442a2efbc9bfc18c41f5ee2b67
  - Rollback `production`: v2 → v1 qua `client.update_prompt(name="day13-chat", version=1, new_labels=["baseline", "production"])`. Request tiếp theo resolve lại đúng version 1 → trace `dfd6a931e00f33c6f1934d5efa0389d2` — https://cloud.langfuse.com/project/cmso4kpzz04grad0cv2tzb2p4/traces/dfd6a931e00f33c6f1934d5efa0389d2
  - Ảnh cần chụp: `submission/evidence/prompt-label-switch.png` và `submission/evidence/prompt-label-rollback.png` (mỗi ảnh: trang prompt version history + trace tương ứng, thấy rõ `prompt_version` trong metadata trace đổi từ 2 → 1)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID: practice-rag-slow
- Triệu chứng từ metrics:
  - Latency P95 tăng vọt từ mức baseline ~150ms lên mức > 13000ms khi chạy chịu tải đồng thời (concurrency 5).
  - Cảnh báo vi phạm ngưỡng SLO Latency (HighLatency_P95) liên tục được kích hoạt.
- Trace ID liên quan: `practice-trace-rag-slow-01` (Giả lập trên Langfuse)
- Log line/correlation ID liên quan:
  - `req-74ca6726` (Latency: 13711.3ms)
  - `req-0c2676d7` (Latency: 13715.4ms)
  - Dòng log mẫu: `{"service": "api", "latency_ms": 2652, "event": "response_sent", "correlation_id": "req-74ca6726", "feature": "qa"}`
- Root cause:
  - Thành phần RAG trong [app/mock_rag.py](file:///c:/DATA/Day13-K3-Observability/app/mock_rag.py) bị chậm (mô phỏng bằng `time.sleep(2.5)`).
  - Lỗi thiết kế: Hàm `time.sleep()` là một hàm đồng bộ gây nghẽn (blocking call). Do uvicorn chạy đơn luồng cho event loop chính, việc gọi hàm đồng bộ này chặn hoàn toàn luồng xử lý của FastAPI, khiến các request đồng thời khác phải xếp hàng chờ và làm tổng thời gian phản hồi thực tế tăng lũy kế lên hơn 13 giây.
- Fix action:
  - Gọi API tắt sự cố thông qua lệnh: `python scripts/inject_incident.py --scenario rag_slow --disable`.
  - Khắc phục mã nguồn: Thay thế blocking sleep bằng `await asyncio.sleep(2.5)` (chuyển sang non-blocking) hoặc đưa tác vụ retrieve đồng bộ vào chạy trong một threadpool riêng sử dụng `run_in_executor`.
- Preventive measure:
  - Cấu hình Timeout tối đa cho kết nối Vector DB / RAG (ví dụ: `timeout=1.5s`).
  - Thiết lập cơ chế Fallback: Nếu RAG bị lỗi hoặc timeout, API sẽ tự động chuyển sang prompt cơ bản không dùng RAG để đảm bảo phản hồi nhanh cho người dùng, bảo vệ SLO.
  - Thêm linter hoặc test cảnh báo việc import/sử dụng các thư viện I/O đồng bộ trên luồng chính FastAPI.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Lan | Tích hợp tracing chi tiết & prompt versioning: thêm `@observe` cho `retrieve`/`generate` để tạo waterfall RAG/LLM; tạo 2 version prompt `day13-chat` trên Langfuse (v1 baseline/production, v2 candidate); chứng minh đổi và rollback label `production` bằng trace ID thật | *(điền sau khi commit)* | Label trên Langfuse prompt là duy nhất theo version — gán label mới cho version khác sẽ tự động gỡ label đó khỏi version cũ, nên chuyển/rollback `production` chỉ cần một lệnh `update_prompt` |
| | | | |
