SAMPLE_MEETINGS = {
    "Sprint Planning — Q2 Release (EN)": """Sprint Planning Meeting
Date: 2025-04-28
Attendees: Alice (PM), Bob (Lead Dev), Carol (QA), David (Designer)

## Agenda
Review backlog, estimate stories, define sprint goal.

## Feature: User Authentication Redesign
Bob noted the current OAuth flow has a 3% login failure rate on the callback handler.
Alice confirmed this is P0 — must be fixed before launch.
Carol raised concern that no automated tests currently cover the OAuth callback.
David will update the login UI mockups to reflect the new password-reset flow.

Action items:
- Bob: Fix OAuth callback handler by May 2
- Carol: Write automated tests for the login flow by May 3
- David: Deliver updated UI mockups by April 30

## Feature: Dashboard Performance
Load time currently averaging 4.2s. Target is under 2s.
Bob proposed lazy loading for chart components. Team agreed to implement and measure.

Action items:
- Bob: Implement lazy loading on dashboard charts by May 5
- Carol: Run performance benchmarks before and after, document results by May 6

## Sprint Goal
Stable authentication and sub-2s dashboard load time by May 9.

## Risks
- Mockup delivery depends on design system update (2-day delay expected)
- OAuth fix may expose deeper session management issues

## Next Meeting
Sprint Review — May 9, 2025 at 10:00 AM
""",

    "Họp Kick-off Dự án — Tháng 4 (VI)": """Họp Kick-off Dự án Tích hợp Thanh Toán
Ngày: 28/04/2025
Thành phần: Tuấn (PM), Minh (Dev Lead), Lan (QA), Hùng (Backend)

## Tổng quan
Dự án tích hợp cổng thanh toán VNPAY và ViettelPay vào hệ thống thương mại điện tử.
Deadline ra mắt: 30/05/2025.

## Thảo luận

Hùng trình bày kiến trúc tích hợp VNPAY. API sandbox đã hoạt động ổn định.
Minh đề xuất tách payment service riêng thay vì nhúng vào monolith hiện tại.
Lan yêu cầu có môi trường staging riêng để test payment flow mà không ảnh hưởng production.
Tuấn xác nhận budget cho server staging đã được duyệt.

Hành động:
- Hùng: Hoàn thành tích hợp VNPAY sandbox trước 05/05
- Minh: Thiết kế API contract cho payment service trước 03/05
- Lan: Soạn test plan cho toàn bộ payment flow trước 07/05
- Tuấn: Làm việc với ViettelPay để lấy API credentials trước 10/05

## Rủi ro
- ViettelPay chưa cung cấp tài liệu API đầy đủ — có thể delay 1 tuần
- Team chưa có kinh nghiệm với webhook retry mechanism

## Quyết định
1. Ưu tiên hoàn thiện VNPAY trước, ViettelPay làm phase 2 nếu cần
2. Dùng mock webhook server cho QA testing giai đoạn đầu

## Họp tiếp theo
Cập nhật tiến độ: 05/05/2025 lúc 9:00 SA
""",
}
