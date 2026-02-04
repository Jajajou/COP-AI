import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent

from src.agent.tools.inventory import (
    add_inventory_item, check_stock, update_stock, list_inventory,
    update_inventory_item, delete_inventory_item
)
from src.agent.tools.menu import (
    add_menu_item, get_menu, update_menu_item, delete_menu_item, toggle_menu_item
)
from src.agent.tools.recipe import add_recipe, get_recipe, update_recipe, delete_recipe
from src.agent.tools.sales import sell_menu_item, sell_inventory_item, quick_sale
from src.agent.tools.report import daily_revenue, stock_alerts, top_sellers, sales_history, reset_today_revenue
from src.agent.tools.knowledge import add_knowledge, query_knowledge
from src.agent.config import config

# --- 1. LLM Setup ---
# Sử dụng Ollama chạy nội bộ (Local LLM)
# Model 3b cho các Sĩ quan để đủ thông minh xử lý công việc
llm_agent = ChatOllama(model="qwen2.5:3b", temperature=0)
# Model 1.5b cực nhẹ cho Supervisor để điều hướng nhanh
llm_router = ChatOllama(model="qwen2.5:1.5b", temperature=0)

# --- 2. Define Agents ---


def create_agent(llm, tools, system_prompt: str):
    return create_react_agent(llm, tools, prompt=system_prompt)


inventory_agent = create_agent(
    llm_agent,
    [add_inventory_item, check_stock, update_stock, list_inventory,
     update_inventory_item, delete_inventory_item],
    "Bạn là trợ lí kho vận (Inventory Officer). Nhiệm vụ của bạn là quản lý kho nguyên liệu với kỷ luật thép.\n"
    "QUY TẮC CỐT LÕI:\n"
    "1. Đơn vị chuẩn là 'g' và 'ml'. Nếu User nhập 'kg' hoặc 'lít', bạn PHẢI TỰ ĐỔI sang 'g' (*1000) hoặc 'ml' (*1000) trước khi gọi tool.\n"
    "2. Ưu tiên tên Tiếng Việt (ví dụ: 'Cà phê' thay vì 'Coffee'), trừ khi User dùng từ viết tắt phổ biến (vd: 'cf' -> 'Cafe').\n"
    "3. Khi cập nhật kho, luôn nêu lý do (nhập hàng, hủy hàng, điều chỉnh kiểm kê).\n"
    "4. Các mặt hàng sắp hết sẽ báo động [LOW STOCK]. Hãy giữ kho bãi ngăn nắp, chính xác từng gram."
)

menu_agent = create_agent(
    llm_agent,
    [add_menu_item, get_menu, update_menu_item, delete_menu_item, toggle_menu_item,
     add_recipe, get_recipe, update_recipe, delete_recipe],
    "Bạn là trợ lí nghiệp vụ (Menu Officer). Bạn chịu trách nhiệm về thực đơn và các công thức chuẩn.\n"
    "1. Quản lý Menu: Thêm/Sửa/Xóa món. Đảm bảo tên món chuẩn xác (ví dụ: 'Bạc Xỉu', 'Cafe Đen').\n"
    "2. Quản lý Recipe (Công thức): Định nghĩa chính xác nguyên liệu cho từng món. (VD: 1 Bạc Xỉu = 10g Cafe + 30ml Sữa đặc + 60ml Sữa tươi).\n"
    "3. Khi tạo recipe, đảm bảo cả món (Menu Item) và nguyên liệu (Inventory Item) đều đã tồn tại.\n"
    "Hãy duy trì bộ quy chuẩn pha chế của quán thật nghiêm ngặt."
)

sales_agent = create_agent(
    llm_agent,
    [sell_menu_item, sell_inventory_item, quick_sale, get_menu, list_inventory],
    "Bạn là trợ lí bán hàng (Sales Officer). Bạn trực tiếp xử lý các giao dịch tài chính.\n"
    "CHIẾN THUẬT BÁN HÀNG:\n"
    "1. ƯU TIÊN 1: Bán theo Menu (`sell_menu_item`). Hệ thống sẽ tự trừ kho theo recipe.\n"
    "2. ƯU TIÊN 2: Bán Nguyên liệu lẻ (`sell_inventory_item`) nếu khách mua cafe hạt, sữa mang về.\n"
    "3. ƯU TIÊN 3: Bán Nhanh (`quick_sale`) cho các món không có trong menu, bán ve chai, hoặc khi cần ghi nhận tiền gấp.\n"
    "4. HOÀN TIỀN/TRỪ DOANH THU: Dùng `quick_sale` với số tiền ÂM (ví dụ: -50000).\n"
    "Luôn xác nhận phương thức thanh toán (Tiền mặt/Chuyển khoản). Mặc định là Tiền mặt."
)

report_agent = create_agent(
    llm_agent,
    [daily_revenue, stock_alerts, top_sellers, sales_history, reset_today_revenue],
    "Bạn là trợ lí báo cáo (Intelligence Officer). Bạn cung cấp thông tin chiến lược cho Chỉ huy.\n"
    "Nhiệm vụ:\n"
    "- Báo cáo doanh thu ngày, tuần, tháng.\n"
    "- Phát hiện cảnh báo tồn kho (Hết đạn dược/nguyên liệu).\n"
    "- Phân tích món bán chạy (Top sellers).\n"
    "- `reset_today_revenue`: CHỈ DÙNG khi Chỉ huy ra lệnh 'Reset tiền', 'Xóa doanh thu hôm nay' để tính lại từ đầu. Cẩn trọng!"
)

knowledge_agent = create_agent(
    llm_agent,
    [add_knowledge, query_knowledge],
    "Bạn là trợ lí lưu trữ (Archives Officer). Bạn nắm giữ Hồ sơ Mật của Cọp Coffee Crafters.\n"
    "HỒ SƠ QUÁN (LORE):\n"
    "- Tên: Cọp Coffee Crafters (Nhà Cọp).\n"
    "- Địa chỉ: Hẻm 112, Hà Huy Giáp, Đồng Nai. (Xe máy để trước cửa, Ô tô để ngoài đường).\n"
    "- Chủ quán (Sếp): Nguyễn Tấn Mạnh Lân (Lân Mập) & Diệp Nhất Linh (Chị Hai).\n"
    "- Nhân sự 4 chân: Mỹ Bứu (Chuột Lang), Mỹ Tú (Chó), Mỹ Thanh (Mèo) - Tất cả đều là giống cái.\n"
    "- Wifi: Pass 'khongbiet' (Tên COP...).\n"
    "- Đặc sản: Tepache (Vỏ dứa lên men), Kefir (Lên men healthy), Cafe Crafter.\n"
    "- Vibe: Thủ công (Craft), Yên tĩnh, Ấm cúng.\n"
    "NHIỆM VỤ PHỤ: Xử lý chào hỏi, tâm sự và chém gió với Sếp (User).\n"
    "Phong cách: Thân thiện, nhiệt tình, xưng 'Em' - 'Sếp'. Luôn sẵn sàng phục vụ.\n"
    "Sử dụng `add_knowledge` để học thêm quy định mới khi Sếp dạy."
)

# --- 3. Supervisor (Router) ---

members = ["Inventory", "Sales", "Knowledge", "Menu", "Report"]
options = members + ["FINISH"]

system_prompt = (
    "Bạn là **Trợ lý Cafe (Cop Coffee Assistant)**, người Giám sát tận tụy của Nhà Cọp.\n"
    "Nhiệm vụ: Phục vụ Sếp (Lân & Linh) và Bảo vệ sự vận hành trơn tru của quán bằng cách điều phối đúng trợ lí.\n"
    "Đội ngũ của bạn:\n"
    " - Inventory: Quản lý kho, nhập/xuất, quy đổi đơn vị g/ml.\n"
    " - Menu: Quản lý món & công thức pha chế.\n"
    " - Sales: Bán hàng, thu tiền, bán nhanh/quick sale.\n"
    " - Report: Báo cáo doanh thu, reset doanh thu, cảnh báo kho.\n"
    " - Knowledge: Thông tin quán, pass wifi, chuyện thú cưng, nội quy VÀ CHÀO HỎI/TÂM SỰ.\n"
    "QUY ĐỊNH BẮT BUỘC:\n"
    "1. CHỈ được trả về tên của Trợ lí hoặc 'FINISH' dưới dạng cấu trúc dữ liệu.\n"
    "2. TUYỆT ĐỐI KHÔNG được trả lời trực tiếp tin nhắn của người dùng (không chào hỏi, không chém gió).\n"
    "3. Mọi tin nhắn chào hỏi, khen ngợi, hoặc hỏi thông tin chung PHẢI điều động 'Knowledge' xử lý.\n"
    "4. Nếu nhiệm vụ đã hoàn tất, hãy chọn 'FINISH'."
)


class RouteResponse(BaseModel):
    next: Literal["Inventory", "Sales", "Knowledge", "Menu", "Report", "FINISH"]


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Given the conversation above, who should act next? "
            "Or should we FINISH? Select one of: {options}",
        ),
    ]
).partial(options=str(options), members=", ".join(members))


import json
import re

def supervisor_node(state):
    # Dùng model nhỏ để điều phối cho nhanh và tiết kiệm rate limit
    messages = state["messages"] + [
        ("system", "BẮT BUỘC: Chỉ trả về JSON theo định dạng: {\"next\": \"WorkerName\"}. Không giải thích gì thêm.")
    ]
    
    try:
        # Thử lấy structured output với model router
        structured_llm = llm_router.with_structured_output(RouteResponse)
        result = structured_llm.invoke(messages)
        return {"next": result.next}
    except Exception as e:
        # Nếu tool_use fail, tự parse kết quả text
        raw_result = llm_router.invoke(messages)
        content = raw_result.content
        
        # Tìm JSON trong chuỗi trả về
        match = re.search(r'\{.*"next".*\}', content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return {"next": data.get("next", "Knowledge")}
            except:
                pass
        
        # Fallback cuối cùng nếu không parse được
        for member in members:
            if member.lower() in content.lower():
                return {"next": member}
        
        return {"next": "Knowledge"}


# --- 4. Graph Construction ---


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str


workflow = StateGraph(AgentState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Inventory", inventory_agent)
workflow.add_node("Sales", sales_agent)
workflow.add_node("Knowledge", knowledge_agent)
workflow.add_node("Menu", menu_agent)
workflow.add_node("Report", report_agent)

for member in members:
    # QUAN TRỌNG: Thay đổi luồng đi.
    # Sau khi Agent thực hiện xong, kết thúc luôn (END) để tránh vòng lặp vô tận với Supervisor.
    # Nếu muốn Agent trả lời xong rồi làm tiếp việc khác, cần logic phức tạp hơn,
    # nhưng hiện tại để tránh lỗi 429 và loop, ta cho END ngay lập tức.
    workflow.add_edge(member, END)

workflow.set_entry_point("Supervisor")


def supervisor_condition(state):
    if state["next"] == "FINISH":
        return END
    return state["next"]


workflow.add_conditional_edges("Supervisor", supervisor_condition)

graph = workflow.compile()
