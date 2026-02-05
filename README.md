# 🐅 Cop Coffee Assistant - Cẩm Nang Hướng Dẫn Sử Dụng

Chào mừng Sếp đến với hệ thống quản lý AI của Nhà Cọp. Để hệ thống hoạt động chính xác nhất, Sếp vui lòng tham khảo các hướng dẫn ra lệnh dưới đây.

---

## 🛠 1. Quản lý Bán Hàng (Sales Agent)
Chuyên xử lý việc lên đơn, tính tiền và trừ kho tự động.

*   **Bán món trong Menu**: 
    *   *Lệnh:* "Bán 2 cf sữa", "Order 1 bạc xỉu thanh toán thẻ", "Khách mua 1 trà đào"
    *   *Lưu ý:* Hệ thống sẽ tự động trừ nguyên liệu trong kho dựa trên công thức.
*   **Bán nhanh (Món không có trong Menu)**:
    *   *Lệnh:* "Bán nhanh 1 cái bánh gấu 20k", "Thu thêm 15k tiền phí ship"
*   **Bán lẻ nguyên liệu**:
    *   *Lệnh:* "Bán lẻ 0.5kg hạt cafe", "Bán 1 chai siro"

---

## 📦 2. Quản lý Kho Hàng (Inventory Agent)
Chuyên theo dõi số lượng nguyên liệu và nhập hàng.

*   **Kiểm tra tồn kho**:
    *   *Lệnh:* "Kho còn bao nhiêu cafe?", "Kiểm tra tồn kho đường", "Liệt kê danh sách kho"
*   **Nhập hàng/Điều chỉnh**:
    *   *Lệnh:* "Nhập thêm 5kg hạt cafe", "Mới mua 10 lon sữa đặc", "Trừ bớt 1kg đường do bị hỏng"
    *   *Tự động quy đổi:* Sếp có thể nhập "1kg" hoặc "1000g", em sẽ tự hiểu.

---

## 📜 3. Menu & Công Thức (Menu Agent)
Quản lý danh sách món bán và cách pha chế.

*   **Xem thực đơn**:
    *   *Lệnh:* "Menu quán có gì?", "Cho xem danh sách món trà"
*   **Tra cứu công thức**:
    *   *Lệnh:* "Công thức làm bạc xỉu là gì?", "Cách pha Matcha Latte như thế nào?"
*   **Chỉnh sửa món**:
    *   *Lệnh:* "Thêm món Trà Vải giá 35k", "Sửa giá Cafe Đen thành 25k", "Tạm ngưng bán món Cacao"

---

## 📊 4. Báo Cáo Doanh Thu (Report Agent)
Xem con số tiền nong và hiệu quả kinh doanh.

*   **Xem doanh thu**:
    *   *Lệnh:* "Doanh thu hôm nay", "Báo cáo chi tiết hôm qua", "Thống kê tiền bán ngày 2026-02-05"
    *   *Nội dung:* Em sẽ liệt kê tổng tiền và danh sách chi tiết các món đã bán.
*   **Món chạy nhất**:
    *   *Lệnh:* "Tuần này món nào bán chạy nhất?", "Top 5 món bán tốt"
*   **Cảnh báo hết hàng**:
    *   *Lệnh:* "Món nào sắp hết?", "Kiểm tra hàng tồn thấp"

---

## 🧠 5. Ghi Nhớ Kiến Thức (Knowledge Agent)
Dạy bot những thông tin riêng của Nhà Cọp.

*   **Dạy bot**:
    *   *Lệnh:* "Ghi nhớ: Pass wifi của quán là 88888888", "Lưu ý: Giờ mở cửa là 7h sáng hằng ngày"
*   **Hỏi lại**:
    *   *Lệnh:* "Pass wifi là gì?", "Quán mở cửa mấy giờ?", "Địa chỉ quán ở đâu?"

---

## 💡 Mẹo nhỏ để Bot thông minh hơn
1.  **Cụ thể số lượng**: Thay vì nói "Bán cafe", hãy nói "Bán **1** cafe đen".
2.  **Tên món chính xác**: Nếu bot không tìm thấy món, Sếp hãy gõ "Xem menu" để copy đúng tên món đó.
3.  **Xử lý lỗi**: Nếu bot phản hồi chậm, Sếp vui lòng đợi vài giây do hệ thống đang xếp hàng (Rate Limiting) để tránh bị khóa API.
4.  **Kết thúc phiên**: Khi đã làm xong việc, Sếp có thể nhắn "Xong rồi" hoặc "Cảm ơn" để em nghỉ ngơi (FINISH).

---
*Chúc Sếp một ngày buôn may bán đắt! 🐅☕*
