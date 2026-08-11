# Kế hoạch phân chia công việc nhóm 5 thành viên (Day 13 — Observability)

Bản kế hoạch phân chia chi tiết nhiệm vụ của từng thành viên theo đúng tiến trình Checkpoint (CP) và thứ tự thực hiện để đảm bảo dự án vận hành mượt mà và tối ưu hóa điểm số theo [RUBRIC.md](file:///c:/DATA/Day13-K3-Observability/RUBRIC.md).

---

## 📋 Tóm tắt phân vai (Roles & Primary Scope)

*   **Thành viên A — Quỳnh (API & Middleware)**: Phát triển hạ tầng logging, xử lý exception và làm giàu request context.
*   **Thành viên B — Biên (Security Engineer)**: Thiết lập bộ lọc PII, các biểu thức chính quy (regex) bảo mật và audit log.
*   **Thành viên C — Nam (Metrics & Dashboard)**: Đo đạc chỉ số, thống kê lỗi hệ thống và thiết kế hợp đồng dashboard YAML.
*   **Thành viên D — Đạt (SRE & Alerts Engineer)**: Thiết lập SLO, xây dựng các tập luật cảnh báo và viết cẩm nang vận hành (Runbook).
*   **Thành viên E — Lan (QA & Chief Investigator)**: Kiểm thử hiệu năng, tích hợp trace chuyên sâu cho LLM/RAG, điều phối xử lý Incident và tổng hợp báo cáo.

---

## 🚀 Tiến trình chi tiết qua các Checkpoint (CP)

### 📌 Checkpoint 0 — Setup và Baseline (0:00 - 0:30)
*Mục tiêu: Đảm bảo toàn bộ nhóm có môi trường chạy được API, cấu hình thành công Langfuse và ghi nhận chỉ số cơ bản ban đầu.*

1.  **Cài đặt & Baseline ban đầu** *(Chịu trách nhiệm chính: **Thành viên E - Lan**)*
    *   Thực hiện cấu hình môi trường theo hướng dẫn [SETUP.md](file:///c:/DATA/Day13-K3-Observability/SETUP.md), cấu hình các biến môi trường cho Langfuse trong file `.env`.
    *   Khởi chạy ứng dụng: `uvicorn app.main:app --reload --env-file .env`.
    *   Chạy load test baseline: `python scripts/load_test.py` để ghi nhận request đầu tiên vào hệ thống.
    *   Chạy script đánh giá ban đầu: `python scripts/validate_logs.py` và lưu lại điểm số baseline làm bằng chứng cho báo cáo.
2.  **Đồng bộ Git & Khởi tạo dự án** *(Chịu trách nhiệm: **Cả nhóm**)*
    *   Mỗi thành viên clone repository của nhóm về máy local, tạo nhánh làm việc riêng và kiểm tra kết nối tới `/health` endpoint của API thành công.

---

### 📌 Checkpoint 1 — Logging và PII (0:30 - 1:30)
*Mục tiêu: Thiết lập định danh request thông suốt, che giấu dữ liệu nhạy cảm của người dùng (PII) và nâng điểm `validate_logs.py` lên tối thiểu 80/100.*

1.  **Phát triển Middleware & Correlation ID** *(Chịu trách nhiệm: **Thành viên A - Quỳnh**)*
    *   Chỉnh sửa file [app/middleware.py](file:///c:/DATA/Day13-K3-Observability/app/middleware.py):
        *   Gọi `clear_contextvars()` ở đầu mỗi request để dọn sạch dữ liệu cũ, tránh rò rỉ thông tin giữa các request.
        *   Đọc `x-request-id` từ Header hoặc tự động sinh mã mới với định dạng `req-<8-char-hex>`.
        *   Sử dụng `bind_contextvars(correlation_id=correlation_id)` của structlog để liên kết mã định danh vào logger context.
        *   Gán mã định danh vào trạng thái của request: `request.state.correlation_id = correlation_id`.
        *   Trả về mã `x-request-id` và thời gian phản hồi `x-response-time-ms` trong Response Headers.
    *   Làm giàu ngữ cảnh log tại API `/chat` trong [app/main.py](file:///c:/DATA/Day13-K3-Observability/app/main.py#L47):
        *   Sử dụng `bind_contextvars` để gán thêm các thông tin: `user_id_hash`, `session_id`, `feature`, `model`, `env`.
    *   **Mở rộng:** Bổ sung một custom Exception Handler trong [app/main.py](file:///c:/DATA/Day13-K3-Observability/app/main.py) để bắt các ngoại lệ chưa được xử lý, ghi log lỗi an toàn kèm Correlation ID và trả về JSON chuẩn cho client với mã lỗi phù hợp (ví dụ: HTTP 500).

2.  **PII Scrubbing & Regex Patterns** *(Chịu trách nhiệm: **Thành viên B - Biên**)*
    *   Chỉnh sửa file [app/pii.py](file:///c:/DATA/Day13-K3-Observability/app/pii.py):
        *   Hoàn thiện và kiểm tra độ chính xác của các Regex để nhận diện Email, Số điện thoại Việt Nam (`phone_vn`), CCCD (`cccd`), và Thẻ tín dụng (`credit_card`).
        *   **Mở rộng:** Bổ sung thêm regex cho các trường hợp như Số hộ chiếu (Passport) và từ khóa địa chỉ Việt Nam để nâng cao tính bảo mật.
    *   Chỉnh sửa file [app/logging_config.py](file:///c:/DATA/Day13-K3-Observability/app/logging_config.py):
        *   Đăng ký bộ lọc PII `scrub_event` vào chuỗi processors của Structlog trong hàm `configure_logging()`.
    *   Kiểm chứng tính bảo mật của log:
        *   Chạy `python scripts/validate_logs.py` để xác nhận điểm đạt >= 80/100.
        *   Kiểm tra thủ công tệp [data/logs.jsonl](file:///c:/DATA/Day13-K3-Observability/data/logs.jsonl) để chắc chắn không còn email, SĐT hay số thẻ thô hiển thị, tất cả phải được thay thế bằng dạng `[REDACTED_...]`.

3.  **Tích hợp đo đạc Error Rate** *(Chịu trách nhiệm: **Thành viên C - Nam**)*
    *   Chỉnh sửa file [app/metrics.py](file:///c:/DATA/Day13-K3-Observability/app/metrics.py):
        *   Bổ sung trường dữ liệu `error_rate_pct` (phần trăm số request bị lỗi trên tổng số traffic) vào hàm `snapshot()`.
        *   Đảm bảo khi gọi endpoint `/metrics`, chỉ số tỷ lệ lỗi được cập nhật chính xác dựa trên hàm `record_error()` và số lượng traffic.

---

### 📌 Checkpoint 2 — Metrics, Traces và Dashboard (1:30 - 2:30)
*Mục tiêu: Dựng dashboard đo đạc 6 nhóm chỉ số đạt chuẩn validator, cấu hình SLO/Alert rules và có đầy đủ traces trên Langfuse.*

1.  **Thiết kế Dashboard 6 nhóm chỉ số** *(Chịu trách nhiệm: **Thành viên C - Nam**)*
    *   Chỉnh sửa file [config/dashboard.yaml](file:///c:/DATA/Day13-K3-Observability/config/dashboard.yaml):
        *   Xây dựng đầy đủ 6 panels: Latency percentiles, Request traffic, Error rate & breakdown (sử dụng chỉ số `error_rate_pct` vừa bổ sung), Cost over time, Input & Output tokens, Quality proxy.
        *   Đảm bảo các panel có đầy đủ thông tin: `title`, `source`, `events`, `fields`, `aggregations`, `query`, `unit`, và `threshold`.
    *   Chạy kiểm định chất lượng cấu hình:
        *   Chạy `python scripts/validate_dashboard.py` cho đến khi kết quả trả về là `HỢP LỆ: 6/6 panel`.

2.  **Thiết lập SLO & Viết Alert Rules, Alert Runbook** *(Chịu trách nhiệm: **Thành viên D - Đạt**)*
    *   **Thiết lập SLO**: Xác định và cấu hình các ngưỡng threshold hợp lý cho 6 chỉ số trên dashboard trong file [config/dashboard.yaml](file:///c:/DATA/Day13-K3-Observability/config/dashboard.yaml) (ví dụ: Latency P95 <= 3000ms, Error rate <= 2%).
    *   **Viết Alert Rules**: Chỉnh sửa file [config/alert_rules.yaml](file:///c:/DATA/Day13-K3-Observability/config/alert_rules.yaml) để định nghĩa 3 cảnh báo dựa trên triệu chứng (symptom-based) thực tế ảnh hưởng tới người dùng (ví dụ: Latency Spike, Error Rate quá cao, RAG Timeout).
    *   **Viết Alert Runbook**: Hoàn thiện file hướng dẫn vận hành [docs/alerts.md](file:///c:/DATA/Day13-K3-Observability/docs/alerts.md) chi tiết cho cả 3 cảnh báo trên. Với từng cảnh báo phải nêu rõ: mức độ nghiêm trọng (severity), ảnh hưởng người dùng, 3 bước kiểm tra nhanh và phương án khắc phục tạm thời (mitigation).

3.  **Tích hợp Tracing chi tiết & Prompt Versioning** *(Chịu trách nhiệm: **Thành viên E - Lan**)*
    *   **Tạo Traces**: Chạy hệ thống để tích lũy tối thiểu 10 traces trên Langfuse có gắn thẻ metadata đầy đủ.
    *   **Prompt Versioning**: Triển khai theo tài liệu [docs/PROMPT_VERSIONING.md](file:///c:/DATA/Day13-K3-Observability/docs/PROMPT_VERSIONING.md). Tạo 2 phiên bản prompt (v1/v2), gán nhãn label (như `production` và `candidate`) và chứng minh việc chuyển đổi/rollback prompt hoạt động tốt trên Langfuse dashboard. Chụp lại ảnh minh họa lưu vào thư mục `submission/evidence/`.
    *   **Mở rộng (Bọc Trace Sub-component)**: Tích hợp sâu tracing cho thành phần RAG và LLM. Sử dụng decorator `@observe` trong các file [app/mock_rag.py](file:///c:/DATA/Day13-K3-Observability/app/mock_rag.py) (hàm `retrieve`) và [app/mock_llm.py](file:///c:/DATA/Day13-K3-Observability/app/mock_llm.py) (hàm `generate`) để hiển thị cấu trúc waterfall phân tách rõ thời gian chạy của RAG và LLM trong Langfuse.

---

### 📌 Checkpoint 3 — Challenge Chính Thức & Điều Tra (2:30 - 3:30)
*Mục tiêu: Kích hoạt sự cố thực tế, phối hợp phát hiện triệu chứng, định vị span lỗi và tìm ra nguyên nhân gốc rễ.*

1.  **Tái hiện sự cố & Thu thập số liệu** *(Chịu trách nhiệm: **Thành viên E - Lan**)*
    *   Khi có file `config/challenge.json` từ Coach, tiến hành chạy lệnh kích hoạt incident:
        `python scripts/inject_incident.py`
    *   Chạy load test với tải trọng cao:
        `python scripts/load_test.py --challenge --concurrency 5`
2.  **Liên kết dữ liệu điều tra (Metrics -> Traces -> Logs)** *(Chịu trách nhiệm: **Cả nhóm - Do Lan điều phối**)*
    *   **Bước 1 (Metrics)**: Nam và Đạt phát hiện triệu chứng bất thường trên Dashboard (ví dụ: Panel Latency tăng vọt hoặc Error Rate tăng đột biến).
    *   **Bước 2 (Traces)**: Lan truy cập Langfuse, tìm các Trace có thời gian xử lý chậm hoặc bị báo đỏ lỗi. Xác định chính xác Span nào (API, RAG, hay LLM) đang gặp vấn đề nhờ vào phần bọc trace sub-component đã làm ở CP2.
    *   **Bước 3 (Logs)**: Quỳnh lấy Correlation ID từ Span bị lỗi trên Langfuse, truy xuất dòng log tương ứng trong [data/logs.jsonl](file:///c:/DATA/Day13-K3-Observability/data/logs.jsonl).
    *   **Bước 4 (Root Cause & Fix)**: Biên và Quỳnh phân tích dữ liệu payload/error trong log để chỉ ra nguyên nhân gốc rễ (ví dụ: do RAG bị chậm, do token LLM bị nhân bản bất thường, hay do lỗi timeout). Đề xuất biện pháp xử lý nóng (Fix action) và giải pháp phòng ngừa lâu dài (Preventive measure).

---

### 📌 Hoàn Tất — Báo Cáo & Demo (3:30 - 4:00)
*Mục tiêu: Đóng gói toàn bộ sản phẩm lab, hoàn thiện báo cáo và sẵn sàng thuyết trình.*

1.  **Hoàn thiện Báo cáo Nhóm** *(Chịu trách nhiệm: **Thành viên E - Lan**)*
    *   Điền đầy đủ thông tin vào file báo cáo nộp bài [submission/REPORT.md](file:///c:/DATA/Day13-K3-Observability/submission/REPORT.md), bao gồm các thông tin nhóm, bảng đóng góp cá nhân, liên kết tới mã nguồn, các mã Trace ID và phần giải trình điều tra sự cố.
    *   Đảm bảo toàn bộ hình ảnh minh chứng (evidence) đã được lưu vào thư mục `submission/evidence/`.
2.  **Kiểm tra an toàn & Bảo mật** *(Chịu trách nhiệm: **Thành viên B - Biên**)*
    *   Chạy rà soát bảo mật thủ công và qua git status để cam kết không đưa các file nhạy cảm như `.env`, các API Key hoặc log chứa thông tin PII nguyên văn chưa được che giấu lên git.
3.  **Kiểm thử tổng thể & Commit** *(Chịu trách nhiệm: **Thành viên A - Quỳnh & Cả nhóm**)*
    *   Chạy bộ test của hệ thống: `python -m pytest -q` và chạy lại validator `python scripts/validate_logs.py` để kiểm tra lần cuối.
    *   Thực hiện commit toàn bộ mã nguồn hợp lệ lên GitHub và lấy mã Commit SHA cuối cùng điền vào báo cáo. Chuẩn bị slide hoặc kịch bản demo nhanh theo luồng: **Metrics → Traces → Logs → Root cause**.

---

## 📅 Bản đồ phân phối công việc theo thành viên (Matrix)

| Thành viên | CP0: Setup & Baseline | CP1: Logging & PII | CP2: Metrics, Traces & Dashboard | CP3: Challenge & Điều tra | Hoàn tất: Report & Demo |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quỳnh (API)** | Hỗ trợ setup môi trường | - Middleware & Correlation ID ([middleware.py](file:///c:/DATA/Day13-K3-Observability/app/middleware.py))<br>- Làm giàu request context ([main.py](file:///c:/DATA/Day13-K3-Observability/app/main.py))<br>- **Mở rộng**: Custom Exception Handler | Viết mã xử lý lỗi bổ sung nếu cần | Truy xuất logs bằng Correlation ID từ span lỗi | Commit code, kiểm thử `pytest` và chuẩn bị demo luồng |
| **Biên (Security)** | Hỗ trợ setup môi trường | - Regex patterns PII ([pii.py](file:///c:/DATA/Day13-K3-Observability/app/pii.py))<br>- Đăng ký PII Processor ([logging_config.py](file:///c:/DATA/Day13-K3-Observability/app/logging_config.py))<br>- Validate logs >= 80 điểm | Hỗ trợ kiểm thử an toàn dashboard | Phân tích logs, đề xuất giải pháp bảo mật dữ liệu | Rà soát bảo mật, đảm bảo không leak secrets/PII lên Git |
| **Nam (Metrics)** | Hỗ trợ setup môi trường | Đo đếm `error_rate_pct` ([metrics.py](file:///c:/DATA/Day13-K3-Observability/app/metrics.py)) | - Thiết kế đặc tả Dashboard ([dashboard.yaml](file:///c:/DATA/Day13-K3-Observability/config/dashboard.yaml))<br>- Chạy `validate_dashboard.py` (6/6 panel) | Theo dõi Metrics/Dashboard phát hiện triệu chứng sự cố | Tổng hợp dữ liệu chỉ số phục vụ viết báo cáo |
| **Đạt (SRE)** | Hỗ trợ setup môi trường | Hỗ trợ kiểm tra định dạng log | - Thiết lập SLO trên Dashboard<br>- Viết Alert Rules ([alert_rules.yaml](file:///c:/DATA/Day13-K3-Observability/config/alert_rules.yaml))<br>- Viết Alert Runbook ([alerts.md](file:///c:/DATA/Day13-K3-Observability/docs/alerts.md)) | Phối hợp với Nam xác định triệu chứng vi phạm SLO | Chuẩn bị phần lý thuyết và quy trình vận hành trong demo |
| **Lan (QA & Leader)** | - Cài đặt Langfuse<br>- Khởi chạy API & Load test<br>- Lưu kết quả baseline | Theo dõi chất lượng logs & kiểm thử liên tục | - Chạy thử Langfuse để có ít nhất 10 traces<br>- Tích hợp Prompt v1/v2 & Rollback<br>- **Mở rộng**: Decorator `@observe` cho RAG & LLM | - Chạy incident & load test chính thức<br>- Sử dụng trace Langfuse định vị span lỗi | - Hoàn thiện báo cáo [REPORT.md](file:///c:/DATA/Day13-K3-Observability/submission/REPORT.md)<br>- Đóng gói bằng chứng tại `submission/evidence/` |
