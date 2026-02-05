# 🐅 Cop Coffee Assistant - Cam Nang Huong Dan Su Dung

Chao mung Sep den voi he thong quan ly AI cua Nha Cop! Bot su dung **Gemini 2.5** (Flash cho agents, Pro cho supervisor) de dieu phoi 5 chuyen vien thong minh qua Telegram.

---

## 🚀 Cai Dat & Khoi Chay

### Yeu cau he thong

| Thanh phan | Phien ban |
|---|---|
| Python | >= 3.11 |
| Docker | Bat ky (de chay PostgreSQL) |
| uv | Package manager (thay pip) |

### Buoc 1: Cau hinh Environment Variables

Tao file `.env` tai thu muc goc du an:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
DATABASE_URL=postgresql+psycopg2://coffee_admin:coffee_password@localhost:5440/coffee_shop
```

| Bien | Mo ta | Bat buoc |
|---|---|---|
| `TELEGRAM_TOKEN` | Token cua Telegram Bot (lay tu @BotFather) | Co |
| `GOOGLE_API_KEY` | API key cua Google AI (Gemini) | Co |
| `DATABASE_URL` | Connection string PostgreSQL (mac dinh da co) | Khong |

### Buoc 2: Khoi chay Database

```bash
docker compose up -d
```

Database se chay tai `localhost:5440`. PGAdmin (giao dien quan ly DB) tai `http://localhost:5050`:
- Email: `admin@coffee.com`
- Password: `admin`

### Buoc 3: Cai dat dependencies

```bash
uv sync
```

### Buoc 4: Chay bot

```bash
python main.py
```

### Windows: Chay tu dong bang script

Neu Sep dung Windows, chi can chay file `start_bot_windows.bat` - script se tu dong kiem tra Docker, khoi dong database, sync dependencies va chay bot.

---

## 🛠 1. Quan Ly Ban Hang (Sales Agent)

Chuyen xu ly viec len don, tinh tien va tru kho tu dong. Co **3 cach ban hang** khac nhau:

### ☕ 1.1. Ban mon trong Menu (`sell_menu_item`)

Ban cac mon da co trong menu. He thong **tu dong tru nguyen lieu** theo cong thuc (back-flushing).

| Lenh mau | Mo ta |
|---|---|
| "Ban 2 cf sua" | Ban 2 ly cafe sua, thanh toan tien mat |
| "Order 1 bac xiu thanh toan the" | Ban 1 bac xiu, thanh toan bang the |
| "Khach mua 1 tra dao chuyen khoan" | Ban 1 tra dao, thanh toan chuyen khoan |

**Phuong thuc thanh toan:** `cash` (tien mat), `card` (the), `transfer` (chuyen khoan)

**Luu y:**
- Bot se tu dong tra menu de tim mon gan dung nhat (khong phan biet hoa thuong, ho tro tim kiem gan dung).
- Neu cong thuc da duoc thiet lap, nguyen lieu se bi tru tu dong.
- Neu nguyen lieu khong du, bot se bao loi va KHONG ghi nhan don.

### 📦 1.2. Ban le nguyen lieu (`sell_inventory_item`)

Ban truc tiep nguyen lieu tu kho. Thich hop khi khach muon mua nguyen lieu roi (hat cafe, siro, bot...).

| Lenh mau | Mo ta |
|---|---|
| "Ban le 0.5kg hat cafe" | Ban 0.5kg cafe tu kho |
| "Ban 1 chai siro" | Ban 1 chai siro tu kho |

**Luu y:**
- Gia ban = `don gia nguyen lieu x so luong`.
- He thong **tru truc tiep tu kho** va ghi log.
- Neu kho khong du, bot se bao loi.

### ⚡ 1.3. Ban nhanh (`quick_sale`)

Ghi nhan doanh thu ma **KHONG tru kho**. Dung cho nhung mon/phi khong co trong he thong.

| Lenh mau | Mo ta |
|---|---|
| "Ban nhanh 1 cai banh gau 20k" | Ghi nhan 20,000 VND |
| "Thu them 15k tien phi ship" | Ghi nhan phi ship |
| "Ban nhanh banh mi 10k" | Mon khong co trong menu |
| "Ban nhanh hoan tien -50k" | Hoan tien khach (so am) |

**Luu y:**
- Ho tro **so am** de hoan tien.
- Chi ghi nhan doanh thu, khong anh huong kho hang.
- Dung cho: mon khong co trong menu/kho, phi them (ship, da vien, tui...), hoan tra.

### 📊 Bang so sanh 3 cach ban hang

| Tieu chi | Ban mon Menu | Ban le Kho | Ban nhanh |
|---|---|---|---|
| **Lenh** | "Ban 1 cf sua" | "Ban le 0.5kg cafe" | "Ban nhanh banh gau 20k" |
| **Tru kho** | Tu dong (theo cong thuc) | Truc tiep | Khong |
| **Can co trong Menu** | Co | Khong | Khong |
| **Can co trong Kho** | Khong bat buoc | Co | Khong |
| **Tinh gia** | Gia menu | Don gia x so luong | Sep tu nhap |
| **Ho tro hoan tien** | Khong | Khong | Co (so am) |
| **Khi nao dung** | Ban mon uong binh thuong | Ban nguyen lieu roi | Mon le, phi them, hoan tra |

---

## 📦 2. Quan Ly Kho Hang (Inventory Agent)

Chuyen theo doi so luong nguyen lieu, nhap hang va canh bao het hang.

### Cac thao tac chinh

| Lenh mau | Thao tac | Tool |
|---|---|---|
| "Kiem kho cafe" | Kiem tra ton kho 1 nguyen lieu | `check_stock` |
| "Liet ke danh sach kho" | Xem toan bo kho hang | `list_inventory` |
| "Nhap them 5kg hat cafe" | Tang so luong (so duong) | `update_stock` |
| "Tru bot 1kg duong do bi hong" | Giam so luong (so am) | `update_stock` |
| "Them nguyen lieu Siro Vani don vi chai gia 50k" | Tao nguyen lieu moi | `add_inventory_item` |
| "Doi ten nguyen lieu X thanh Y" | Cap nhat thong tin | `update_inventory_item` |
| "Xoa nguyen lieu Z" | Xoa vinh vien khoi kho | `delete_inventory_item` |

### Tinh nang dac biet

- **Tu dong quy doi don vi:** Sep co the nhap "1kg" hoac "1000g", "1L" hoac "1000ml" - bot se tu hieu.
- **Canh bao ton kho thap (`min_alert`):** Khi them nguyen lieu, Sep co the dat muc canh bao. Vi du: "Them cafe don vi kg gia 200k canh bao khi duoi 2kg". Khi ton kho chung hoac duoi muc nay, he thong se hien `[IT]` hoac `[SAP HET HANG]`.
- **Audit Log:** Moi thay doi kho deu duoc ghi lai (ly do, so luong, thoi gian) trong bang `inventory_logs`.

---

## 📜 3. Menu & Cong Thuc (Menu Agent)

Quan ly danh sach mon ban, gia ca, phan loai va cong thuc pha che.

### Quan ly Menu

| Lenh mau | Thao tac | Tool |
|---|---|---|
| "Menu quan co gi?" | Xem toan bo menu | `get_menu` |
| "Cho xem danh sach mon Do uong nong" | Loc theo danh muc | `get_menu` |
| "Them mon Tra Vai gia 35k vao danh muc Do uong lanh" | Them mon moi | `add_menu_item` |
| "Sua gia Cafe Den thanh 25k" | Cap nhat thong tin mon | `update_menu_item` |
| "Tam ngung ban mon Cacao" | Tat/bat trang thai mon | `toggle_menu_item` |
| "Xoa mon ABC khoi menu" | Xoa vinh vien | `delete_menu_item` |

**Danh muc co san:** "Do uong nong", "Do uong lanh", "Thuc an", "Chung" (hoac tu tuy chinh).

### Quan ly Cong Thuc

| Lenh mau | Thao tac | Tool |
|---|---|---|
| "Xem cong thuc Bac Xiu" | Xem nguyen lieu can dung | `get_recipe` |
| "Cong thuc Latte can 0.02kg cafe va 0.2L sua" | Them cong thuc | `add_recipe` |
| "Cap nhat cong thuc: Latte can 0.03kg cafe" | Sua so luong | `update_recipe` |
| "Xoa bot sua khoi cong thuc Latte" | Go nguyen lieu | `delete_recipe` |

**Luu y:** Cong thuc lien ket **mon trong menu** voi **nguyen lieu trong kho**. Khi ban mon, he thong dua vao cong thuc de tu dong tru kho.

---

## 📊 4. Bao Cao Doanh Thu (Report Agent)

Xem so lieu tien nong va hieu qua kinh doanh.

| Lenh mau | Mo ta | Tool |
|---|---|---|
| "Doanh thu hom nay" | Tong doanh thu + chi tiet tung mon | `daily_revenue` |
| "Bao cao chi tiet ngay 2026-02-01" | Doanh thu ngay cu the (YYYY-MM-DD) | `daily_revenue` |
| "Top 5 mon ban chay tuan nay" | Xep hang mon ban chay (tuy chinh days/limit) | `top_sellers` |
| "Mon nao sap het hang?" | Nguyen lieu duoi nguong canh bao | `stock_alerts` |
| "Lich su 7 ngay gan day" | Doanh thu theo ngay | `sales_history` |
| "Reset doanh thu hom nay" | XOA toan bo doanh thu hom nay | `reset_today_revenue` |

**Chi tiet bao cao doanh thu (`daily_revenue`):**
- Tong hop tu 3 nguon: don hang Menu (Order), ban le Kho (INVENTORY), ban nhanh (QUICK).
- Liet ke chi tiet tung mon da ban, so luong, thanh tien.

**Canh bao:** `reset_today_revenue` se **XOA VINH VIEN** toan bo don hang va ghi nhan ban hang trong ngay. Hanh dong nay **KHONG THE HOAN TAC**.

---

## 🧠 5. Ghi Nho Kien Thuc (Knowledge Agent)

Day bot nhung thong tin rieng cua Nha Cop. Su dung ChromaDB lam vector store voi sentence-transformer embeddings.

| Lenh mau | Thao tac | Tool |
|---|---|---|
| "Ghi nho: Pass wifi cua quan la 88888888" | Luu kien thuc moi | `add_knowledge` |
| "Luu y: Gio mo cua la 7h sang hang ngay" | Luu kien thuc moi | `add_knowledge` |
| "Pass wifi la gi?" | Truy van kien thuc | `query_knowledge` |
| "Quan mo cua may gio?" | Truy van kien thuc | `query_knowledge` |
| "Dia chi quan o dau?" | Truy van kien thuc | `query_knowledge` |

**Luu y:**
- Du lieu luu tai `./knowledge_db/` (persistent).
- Tra ve top 3 ket qua gan dung nhat (semantic search).
- Neu cung topic, noi dung moi se **ghi de** noi dung cu (upsert).

---

## 💡 Meo Su Dung

### Phan biet 3 cach ban hang (QUAN TRONG)

| Tinh huong | Cach lam |
|---|---|
| Ban mon co trong menu, muon tru nguyen lieu | "Ban 1 cf sua" |
| Ban nguyen lieu roi tu kho | "Ban le 0.5kg cafe" |
| Ban mon/phi khong co trong he thong | "Ban nhanh banh gau 20k" |
| Hoan tien cho khach | "Ban nhanh hoan tien -50k" |
| Thu phi them (ship, da, tui...) | "Ban nhanh phi ship 15k" |

### Alias thong minh

Bot tu dong hieu cac tu viet tat pho bien:
- "cf" → "Cafe"
- "cf den" → "Cafe Den"
- "den da" → "Cafe Den"
- "cf sua" → "Cafe Sua"

Neu bot khong nhan ra ten mon, hay noi **"Xem menu"** de copy dung ten.

### Meo chung

1. **Cu the so luong**: Thay vi noi "Ban cafe", hay noi "Ban **1** cafe den".
2. **Ten mon chinh xac**: Neu bot khong tim thay mon, go "Xem menu" de copy dung ten.
3. **Xu ly loi**: Neu bot phan hoi cham, vui long doi vai giay do he thong dang xep hang (Rate Limiting) de tranh bi khoa API.
4. **Ket thuc phien**: Khi da xong viec, nhan "Xong roi" hoac "Cam on" de bot nghi ngoi (FINISH).

---

## ❓ Tinh Huong Thuong Gap (FAQ)

**Q: Toi muon ban mon khong co trong menu ma khong can them vao menu?**
A: Dung lenh ban nhanh: "Ban nhanh [ten mon] [gia]". Vi du: "Ban nhanh banh mi thit 25k". Don hang se duoc ghi nhan doanh thu nhung khong tru kho.

**Q: Toi muon ban nguyen lieu roi (hat cafe, siro...) cho khach?**
A: Dung lenh ban le: "Ban le [so luong] [ten nguyen lieu]". Vi du: "Ban le 0.5kg hat cafe". He thong se tu tinh gia theo don gia va tru kho.

**Q: Lam sao de hoan tien cho khach?**
A: Dung ban nhanh voi so am: "Ban nhanh hoan tien khach -50k". So tien am se duoc tru khoi doanh thu.

**Q: Mon da co trong menu nhung khong co cong thuc, ban co bi loi khong?**
A: Khong. He thong van ghi nhan don hang va doanh thu binh thuong, chi la khong tru nguyen lieu (vi khong co cong thuc de tru).

**Q: Lam sao biet nguyen lieu nao sap het?**
A: Nhan "Mon nao sap het hang?" hoac "Kiem tra hang ton thap". He thong se liet ke cac nguyen lieu duoi nguong `min_alert`.

**Q: Toi muon xoa toan bo doanh thu hom nay de nhap lai tu dau?**
A: Nhan "Reset doanh thu hom nay". **Luu y: Khong the hoan tac!**

---

## 🏗 Kien Truc He Thong

### Tong quan

```
Tin nhan tu Telegram
    → main.py (Telegram handler, luu lich su hoi thoai)
    → graph.ainvoke()
    → Supervisor Node (Gemini 2.5 Pro - dieu phoi)
    → Agent Node (Gemini 2.5 Flash - thuc thi tools)
    → Response tra ve Telegram
```

### Mo hinh LLM

| Vai tro | Model | Ly do |
|---|---|---|
| Supervisor (dieu phoi) | Gemini 2.5 Pro | Phan tich chinh xac, dieu huong dung agent |
| Agents (thuc thi) | Gemini 2.5 Flash | Phan hoi nhanh, tiet kiem chi phi |

### 5 Agents

| Agent | Vai tro | Tools |
|---|---|---|
| **Inventory** | Kho hang | `add_inventory_item`, `check_stock`, `update_stock`, `list_inventory`, `update_inventory_item`, `delete_inventory_item` |
| **Sales** | Ban hang | `sell_menu_item`, `sell_inventory_item`, `quick_sale`, `get_menu`, `list_inventory` |
| **Menu** | Thuc don & Cong thuc | `add_menu_item`, `get_menu`, `update_menu_item`, `delete_menu_item`, `toggle_menu_item`, `add_recipe`, `get_recipe`, `update_recipe`, `delete_recipe` |
| **Report** | Bao cao | `daily_revenue`, `stock_alerts`, `top_sellers`, `sales_history`, `reset_today_revenue` |
| **Knowledge** | Kien thuc | `add_knowledge`, `query_knowledge` |

### Database Schema (PostgreSQL)

| Bang | Mo ta |
|---|---|
| `inventory_items` | Nguyen lieu (ten, don vi, so luong, don gia, min_alert) |
| `menu_items` | Mon trong menu (ten, gia, mo ta, danh muc, trang thai) |
| `recipes` | Cong thuc (mon → nguyen lieu, so luong can) |
| `orders` | Don hang (tong tien, phuong thuc thanh toan, thoi gian) |
| `order_items` | Chi tiet don hang (mon, so luong, gia tai thoi diem ban) |
| `inventory_logs` | Lich su thay doi kho (nguyen lieu, so luong, ly do, thoi gian) |
| `sales` | Ghi nhan ban hang (ten, so luong, tong tien, loai: MENU/INVENTORY/QUICK) |

### Cau truc thu muc

```
COP_COFFEE_ASSISTANT/
├── main.py                          # Entry point - Telegram bot handler
├── docker-compose.yml               # PostgreSQL + PGAdmin
├── pyproject.toml                    # Dependencies (uv)
├── langgraph.json                    # LangGraph Platform config
├── start_bot_windows.bat             # Script khoi dong tu dong (Windows)
├── .env                              # Environment variables (khong commit)
├── knowledge_db/                     # ChromaDB persistent storage
├── postgres_data/                    # PostgreSQL data (khong commit)
└── src/agent/
    ├── graph.py                      # LangGraph workflow: supervisor + 5 agents
    ├── config.py                     # Load & validate env vars
    ├── domain/
    │   └── models.py                 # SQLAlchemy models (7 bang)
    ├── clients/
    │   └── postgres.py               # Database engine, session factory, init_db()
    └── tools/
        ├── inventory.py              # 6 tools quan ly kho
        ├── menu.py                   # 5 tools quan ly menu
        ├── recipe.py                 # 4 tools quan ly cong thuc
        ├── sales.py                  # 3 tools ban hang
        ├── report.py                 # 5 tools bao cao
        └── knowledge.py              # 2 tools kien thuc (ChromaDB)
```

---

*Chuc Sep mot ngay buon may ban dat! 🐅☕*
