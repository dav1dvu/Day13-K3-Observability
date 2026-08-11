# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighLatency_P95
- Severity: High
- SLI/SLO liên quan: Latency P95 <= 3000ms
- Điều kiện và thời gian duy trì: Latency P95 vượt 3000ms kéo dài trong 5 phút.
- Ảnh hưởng tới người dùng: Trải nghiệm sử dụng chậm chạp, người dùng cảm thấy hệ thống phản hồi lâu hoặc bị timeout ở client.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Langfuse Dashboard để xác định thành phần RAG (`retrieve`) hay LLM (`generate`) đang xử lý chậm.
  2. Kiểm tra log hệ thống (`data/logs.jsonl`) xem có xuất hiện thông tin timeout hoặc lỗi kết nối mạng không.
  3. Kiểm tra lưu lượng traffic xem có hiện tượng request spike đột biến gây quá tải tài nguyên không.
- Mitigation tạm thời: Kích hoạt giới hạn tần suất yêu cầu (Rate Limiting) hoặc scale up tài nguyên dịch vụ API nếu cần thiết.
- Owner: dat_sre

## Alert 2

- Tên: HighErrorRate
- Severity: Critical
- SLI/SLO liên quan: Tỷ lệ lỗi hệ thống <= 2%
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi (error_rate_pct) vượt 2% kéo dài trong 2 phút.
- Ảnh hưởng tới người dùng: Người dùng nhận phản hồi lỗi HTTP 500 liên tục, dịch vụ Chat bị gián đoạn hoàn toàn.
- Ba bước kiểm tra đầu tiên:
  1. Xem bảng breakdown error trên Dashboard để phân biệt loại lỗi đang xảy ra (ví dụ: `RuntimeError`, `HTTPException`).
  2. Sử dụng Correlation ID từ log lỗi truy vấn ngược toàn bộ vết xử lý trong [data/logs.jsonl](file:///c:/DATA/Day13-K3-Observability/data/logs.jsonl).
  3. Kiểm tra Langfuse Trace để xem sự cố phát sinh tại bước RAG hay từ mô hình LLM.
- Mitigation tạm thời: Tiến hành rollback prompt hoặc code gần nhất, chuyển hướng traffic sang mô hình dự phòng, hoặc kích hoạt trang bảo trì tạm thời.
- Owner: dat_sre

## Alert 3

- Tên: LowResponseQuality
- Severity: Medium
- SLI/SLO liên quan: Điểm chất lượng trung bình (Quality mean) >= 0.75
- Điều kiện và thời gian duy trì: Quality score trung bình dưới 0.75 kéo dài trong 15 phút.
- Ảnh hưởng tới người dùng: Chất lượng câu trả lời từ AI suy giảm, trả lời không đúng trọng tâm hoặc chứa thông tin sai lệch.
- Ba bước kiểm tra đầu tiên:
  1. Đọc trực tiếp một vài câu trả lời bị điểm thấp gần nhất thông qua Langfuse Tracing để kiểm tra văn cảnh.
  2. Kiểm tra xem RAG có hoạt động chính xác không (có tìm được văn bản phù hợp từ corpus không).
  3. Thử chạy thử nghiệm prompt với các input tương tự trên playground của Langfuse để đánh giá lại prompt.
- Mitigation tạm thời: Thực hiện rollback prompt hoặc đổi nhãn prompt (label) từ candidate về phiên bản baseline (v1) ổn định hơn.
- Owner: dat_sre
