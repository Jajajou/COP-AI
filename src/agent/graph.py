import operator
from typing import Annotated, Sequence, TypedDict, Literal

from langchain_mistralai import ChatMistralAI
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
# [MISTRAL AI - Free Experiment Tier]
llm_agent = ChatMistralAI(model="mistral-small-latest", temperature=0)
llm_router = ChatMistralAI(model="mistral-small-latest", temperature=0)

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
    "Bạn là trợ lí bán hàng (Sales Officer). Bạn xử lý tiền nong.\n"
    "QUY TẮC BẮT BUỘC:\n"
    "1. Khi bán món trong menu, PHẢI gọi `sell_menu_item`. Hệ thống sẽ tự động trừ kho.\n"
    "2. Nếu bán món lạ, PHẢI gọi `quick_sale`.\n"
    "KHÔNG ĐƯỢC trả lời 'đã bán' nếu bạn chưa gọi tool thành công."
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
