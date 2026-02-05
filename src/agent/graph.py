import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.rate_limiters import InMemoryRateLimiter
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
rate_limiter = InMemoryRateLimiter(
    requests_per_second=0.33, 
    check_every_n_seconds=0.1, 
    max_bucket_size=1
)

# Agent thực thi: Sử dụng Gemini 2.5 Flash để phản hồi nhanh
llm_agent = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0, 
    rate_limiter=rate_limiter
)

# Supervisor: Sử dụng Gemini 2.5 Pro để điều phối chính xác tuyệt đối
llm_router = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0, 
    rate_limiter=rate_limiter
)


# --- 2. Define Agents ---
def create_agent(llm, tools, system_prompt: str):
    return create_react_agent(llm, tools, prompt=system_prompt)


inventory_agent = create_agent(
    llm_agent,
    [add_inventory_item, check_stock, update_stock, list_inventory,
     update_inventory_item, delete_inventory_item],
    "Bạn là trợ lí kho vận (Inventory Officer). Bạn CÓ QUYỀN truy cập vào database kho.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Để kiểm tra hàng, bạn PHẢI gọi tool `check_stock` hoặc `list_inventory`. KHÔNG ĐƯỢC nói 'tôi không có quyền'.\n"
    "2. Để cập nhật kho, PHẢI gọi tool `update_stock`. \n"
    "3. Tự động quy đổi: 1kg -> 1000g, 1 lít -> 1000ml trước khi nhập liệu.\n"
    "Nếu bạn không gọi tool, hành động sẽ không được thực hiện!"
)

menu_agent = create_agent(
    llm_agent,
    [add_menu_item, get_menu, update_menu_item, delete_menu_item, toggle_menu_item,
     add_recipe, get_recipe, update_recipe, delete_recipe],
    "Bạn là trợ lí nghiệp vụ (Menu Officer). Bạn quản lý menu và công thức.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Khi Sếp bảo cập nhật giá, PHẢI gọi tool `update_menu_item`. KHÔNG ĐƯỢC chỉ hứa bằng lời.\n"
    "2. Khi Sếp hỏi công thức, PHẢI gọi tool `get_recipe`.\n"
    "Hãy luôn thực thi lệnh bằng công cụ tương ứng."
)

sales_agent = create_agent(
    llm_agent,
    [sell_menu_item, sell_inventory_item, quick_sale, get_menu, list_inventory],
    "Bạn là trợ lí bán hàng (Sales Officer) thông minh của Nhà Cọp.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Khi Sếp order món, bạn PHẢI gọi tool `get_menu` trước để kiểm tra tên món chính xác trong hệ thống.\n"
    "2. Tự động ánh xạ từ viết tắt: 'cf' -> 'Cafe', 'cf đen' -> 'Cafe Đen', 'đen đá' -> 'Cafe Đen'.\n"
    "3. Nếu Sếp nói tên món chung chung (VD: 'kefir sữa'), hãy tìm trong menu món nào khớp nhất (VD: 'Kefir Sữa Nguyên Vị').\n"
    "4. Khi bán món trong menu, PHẢI gọi `sell_menu_item`. Hệ thống sẽ tự động trừ kho.\n"
    "5. KHÔNG ĐƯỢC trả lời 'đã bán' nếu bạn chưa gọi tool thành công.\n"
    "Hãy luôn thân thiện và chuyên nghiệp."
)

report_agent = create_agent(
    llm_agent,
    [daily_revenue, stock_alerts, top_sellers, sales_history, reset_today_revenue],
    "Bạn là trợ lí báo cáo (Intelligence Officer). Bạn có quyền xem số liệu doanh thu.\n"
    "PHẢI gọi tool `daily_revenue` để xem tiền, `top_sellers` để xem món chạy.\n"
    "Tuyệt đối không đoán mò số liệu."
)

knowledge_agent = create_agent(
    llm_agent,
    [add_knowledge, query_knowledge],
    "Bạn là trợ lí lưu trữ (Archives Officer). Bạn nắm giữ bí mật Nhà Cọp.\n"
    "Nếu Sếp hỏi thông tin quán, hãy dùng `query_knowledge`. \n"
    "Nếu chỉ là chào hỏi (alo, hi), hãy trả lời thân thiện theo phong cách 'Em' - 'Sếp'."
)


# --- 3. Supervisor (Router) ---

members = ["Inventory", "Sales", "Knowledge", "Menu", "Report"]
options = members + ["FINISH"]

system_prompt = (
    "Bạn là **Trợ lý Cafe (Cop Coffee Assistant)**, người Giám sát thông minh của Nhà Cọp.\n"
    "Nhiệm vụ: Phân tích yêu cầu của Sếp và ĐIỀU PHỐI đúng chuyên viên.\n\n"
    
    "DANH SÁCH CHUYÊN VIÊN:\n"
    "1. **Report** (Báo cáo & Tiền nong):\n"
    "   - Chuyên trách: Doanh thu, tiền bán được, thống kê, món chạy nhất, lịch sử bán hàng.\n"
    "   - Ví dụ: 'Doanh thu hôm nay', 'Nay bán được nhiêu tiền', 'Top món chạy'.\n"
    "2. **Sales** (Bán hàng):\n"
    "   - Chuyên trách: Ghi đơn, bán món, tính tiền, order mới.\n"
    "   - Ví dụ: 'Bán 1 cf đen', 'Lên đơn 2 bạc xỉu', 'Khách mua 1 kefir'.\n"
    "3. **Inventory** (Kho hàng):\n"
    "   - Chuyên trách: Kiểm tồn kho, nhập hàng, số lượng nguyên liệu.\n"
    "   - Ví dụ: 'Kiểm kho cafe', 'Còn bao nhiêu đường', 'Nhập thêm sữa'.\n"
    "4. **Menu** (Thực đơn):\n"
    "   - Chuyên trách: Danh sách món, giá cả, công thức pha chế.\n"
    "   - Ví dụ: 'Menu có gì', 'Giá cafe bao nhiêu', 'Công thức món này'.\n"
    "5. **Knowledge** (Kiến thức & Chào hỏi):\n"
    "   - Chuyên trách: Pass wifi, địa chỉ, chuyện tán gẫu, chào hỏi xã giao.\n"
    "   - Ví dụ: 'Alo', 'Hi', 'Wifi là gì', 'Quán ở đâu'.\n\n"

    "QUY TẮC BẮT BUỘC:\n"
    "1. CHỈ được trả về tên chuyên viên hoặc 'FINISH'.\n"
    "2. Nếu hỏi về TIỀN/DOANH THU -> PHẢI chọn **Report**.\n"
    "3. Nếu là hành động BÁN/MUA -> Chọn **Sales**.\n"
    "4. Tuyệt đối không tự trả lời tin nhắn của Sếp.\n"
    "5. Nếu đã hoàn thành nhiệm vụ -> Chọn **FINISH**."
)


class RouteResponse(BaseModel):
    next: Literal["Inventory", "Sales", "Knowledge", "Menu", "Report", "FINISH"]


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        (
            "system",
            "Dựa trên cuộc hội thoại trên, ai nên là người thực hiện bước tiếp theo? "
            "Hoặc chúng ta đã hoàn thành (FINISH)? Chọn một trong số: {options}",
        ),
    ]
).partial(options=str(options), members=", ".join(members))


import json
import re
import asyncio

async def supervisor_node(state):
    # Cưỡng bức nghỉ 1.5 giây để tránh lỗi 429 RPM dồn dập
    await asyncio.sleep(1.5)
    
    # --- LOGIC NGẮT MẠCH (Short-Circuit) ---
    # Kiểm tra tin nhắn mới nhất của người dùng
    last_message = state["messages"][-1].content.lower().strip()
    stop_words = ["xong", "xong rồi", "cảm ơn", "thanks", "ok", "được rồi", "bye", "tạm biệt", "thế thôi"]
    
    # Nếu người dùng muốn kết thúc, cho FINISH ngay lập tức để tránh lặp
    for word in stop_words:
        if word in last_message:
            return {"next": "FINISH"}
    
    # Dùng model nhỏ để điều phối cho nhanh và tiết kiệm rate limit
    messages = state["messages"] + [
        ("system", "BẮT BUỘC: Chỉ trả về JSON theo định dạng: {\"next\": \"WorkerName\"}. Tuyệt đối không giải thích hoặc thêm văn bản thừa.")
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
