from typing import Literal, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.errors import Interrupt
from langgraph.checkpoint.memory import InMemorySaver
import uuid
from datetime import datetime

# Định nghĩa State
class TextReviewState(BaseModel):
    """State cho việc review text"""
    original_text: str = ""
    current_text: str = ""
    review_history: List[dict] = Field(default_factory=list)
    is_approved: bool = False
    step_count: int = 0

# Node: Tạo text cần review
def create_text(state: TextReviewState):
    """Tạo hoặc nhận text cần review"""
    print(f"\U0001f527 [create_text] Executing - Step count: {state.step_count}")
    
    if not state.original_text:
        # Nếu chưa có text, tạo text mẫu
        sample_text = """
Kính gửi Quý khách hàng,

Chúng tôi xin thông báo về việc nâng cấp hệ thống sẽ diễn ra vào ngày 15/09/2025 từ 2:00 đến 4:00 sáng. 
Trong thời gian này, dịch vụ có thể bị gián đoạn tạm thời.

Chúng tôi xin lỗi vì sự bất tiện này và cảm ơn sự thông cảm của Quý khách.

Trân trọng,
Đội ngũ Hỗ trợ Khách hàng
        """.strip()
        
        print(f"\U0001f4dd [create_text] Created sample text: {len(sample_text)} chars")
        return {
            "original_text": sample_text,
            "current_text": sample_text,
            "step_count": state.step_count + 1
        }
    
    print(f"\U0001f4dd [create_text] Using existing text: {len(state.original_text)} chars")
    return {"step_count": state.step_count + 1}

# Node: Human Review với Interrupt
def human_review(state: TextReviewState) -> Command[Literal["process_feedback", "__end__"]]:
    """Node chính cho human review với interrupt"""
    
    print(f"\U0001f464 [human_review] Starting review - Step: {state.step_count}")
    
    # Tăng step count
    step_count = state.step_count + 1
    
    # Tạo description cho interrupt
    description = f"""
# \U0001f4dd Text Review - Bước {step_count}

## Text hiện tại:
{state.current_text}
## Lịch sử thay đổi:
{format_review_history(state.review_history)}

---
**Hành động:**
- ✅ **Approve**: Chấp nhận text này
- ✏️ **Edit**: Chỉnh sửa text  
- \U0001f6ab **Reject**: Từ chối và kết thúc
- \U0001f4ac **Feedback**: Đưa ra nhận xét để cải thiện
"""

    # Cấu hình interrupt
    request = {
        "action_request": {
            "action": "review_text",
            "args": {
                "text": state.current_text,
                "step": step_count
            }
        },
        "config": {
            "allow_accept": True,      # Approve
            "allow_edit": True,        # Edit
            "allow_ignore": True,      # Reject  
            "allow_respond": True      # Feedback
        },
        "description": description
    }
    
    print(f"⏸️ [human_review] Sending interrupt request...")
    
    # Gửi interrupt và nhận response
    response = interrupt([request])[0]
    
    print(f"\U0001f4e8 [human_review] Received response: {response['type']}")
    
    # Xử lý response và chuẩn bị update state
    if response["type"] == "accept":
        # Approve - kết thúc workflow
        print(f"✅ [human_review] Text approved!")
        update = {
            "is_approved": True,
            "step_count": step_count,
            "review_history": state.review_history + [{
                "step": step_count,
                "action": "approved",
                "comment": "Text đã được chấp nhận",
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        goto = END
        
    elif response["type"] == "edit":
        # Edit - cập nhật text và tiếp tục
        edited_text = response["args"]["args"]["text"]
        print(f"✏️ [human_review] Text edited: {len(edited_text)} chars")
        update = {
            "current_text": edited_text,
            "step_count": step_count,
            "review_history": state.review_history + [{
                "step": step_count,
                "action": "edited",
                "comment": "Text đã được chỉnh sửa",
                "old_text": state.current_text[:100] + "..." if len(state.current_text) > 100 else state.current_text,
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        goto = "process_feedback"
        
    elif response["type"] == "ignore":
        # Reject - kết thúc workflow
        print(f"\U0001f6ab [human_review] Text rejected!")
        update = {
            "step_count": step_count,
            "review_history": state.review_history + [{
                "step": step_count,
                "action": "rejected",
                "comment": "Text đã bị từ chối",
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        goto = END
        
    elif response["type"] == "response":
        # Feedback - ghi nhận và tiếp tục review
        feedback = response["args"]
        print(f"\U0001f4ac [human_review] Feedback received: {feedback[:50]}...")
        update = {
            "step_count": step_count,
            "review_history": state.review_history + [{
                "step": step_count,
                "action": "feedback",
                "comment": feedback,
                "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            }]
        }
        goto = "process_feedback"
    
    else:
        raise ValueError(f"Unknown response type: {response['type']}")
    
    print(f"➡️ [human_review] Going to: {goto}")
    return Command(goto=goto, update=update)

# Node: Xử lý feedback và quyết định next step
def process_feedback(state: TextReviewState) -> Command[Literal["human_review", "__end__"]]:
    """Xử lý feedback và quyết định bước tiếp theo"""
    
    print(f"\U0001f504 [process_feedback] Processing step {state.step_count}")
    
    # Kiểm tra điều kiện dừng
    if state.step_count >= 5:  # Giới hạn tối đa 5 bước review
        print(f"⏰ [process_feedback] Maximum steps reached!")
        return Command(
            goto=END,
            update={
                "review_history": state.review_history + [{
                    "step": state.step_count + 1,
                    "action": "timeout",
                    "comment": "Đã đạt giới hạn số bước review",
                    "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
                }]
            }
        )
    
    # Tiếp tục review
    print(f"\U0001f504 [process_feedback] Continuing to human_review")
    return Command(goto="human_review")

# Helper function
def format_review_history(history: List[dict]) -> str:
    """Format lịch sử review để hiển thị"""
    if not history:
        return "*Chưa có lịch sử review*"
    
    formatted = ""
    for entry in history:
        action_emoji = {
            "approved": "✅",
            "edited": "✏️", 
            "rejected": "\U0001f6ab",
            "feedback": "\U0001f4ac",
            "timeout": "⏰"
        }.get(entry["action"], "\U0001f4dd")
        
        formatted += f"\n{action_emoji} **Bước {entry['step']}** ({entry['timestamp']}): {entry['comment']}"
    
    return formatted

# Tạo graph
def create_text_review_graph():
    """Tạo graph cho text review với HITL"""
    
    print("\U0001f3d7️ Creating text review graph...")
    checkpointer = InMemorySaver()
    # Khởi tạo StateGraph
    graph_builder = StateGraph(TextReviewState)
    
    # Thêm nodes
    graph_builder.add_node("create_text", create_text)
    graph_builder.add_node("human_review", human_review)
    graph_builder.add_node("process_feedback", process_feedback)
    
    # Thêm edges
    graph_builder.add_edge(START, "create_text")
    graph_builder.add_edge("create_text", "human_review")
    
    # Compile với checkpointer
    graph = graph_builder.compile(checkpointer=checkpointer)
    
    print("✅ Graph created successfully!")
    return graph

# Demo function sử dụng invoke
def run_text_review_demo():
    """Demo text review sử dụng graph.invoke"""
    
    print("\U0001f4dd Human-in-the-Loop Text Review Demo (using invoke)")
    print("=" * 60)
    print(f"\U0001f550 Started at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"\U0001f464 User: thaodtp2416615")
    
    # Tạo graph
    graph = create_text_review_graph()
    
    # Tạo thread config
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\U0001f9f5 Thread ID: {thread_id}")
    
    # Custom text cho demo
    custom_text = """
Thông báo: Hệ thống sẽ bảo trì vào ngày mai từ 1AM đến 3AM. 
Mọi người chú ý nhé!
    """.strip()
    
    initial_state = TextReviewState(
        original_text=custom_text,
        current_text=custom_text
    )
    
    print(f"\n\U0001f4c4 Initial Text ({len(custom_text)} chars):")
    print("-" * 40)
    print(custom_text)
    
    # Bước 1: Khởi tạo và chạy đến interrupt đầu tiên
    print(f"\n\U0001f680 Step 1: Running until first interrupt...")
    print("=" * 50)
    
    result = graph.invoke(initial_state, config=config)
    
    print(f"\n\U0001f504 Between two invoke calls - Current state:")
    print(f"   \U0001f4ca Step count: {result.get('step_count', 'unknown')}")
    print(f"   \U0001f4dd Text length: {len(result.get('current_text', ''))}")
    print(f"   ✅ Approved: {result.get('is_approved', False)}")
    print(f"   \U0001f4da History entries: {len(result.get('review_history', []))}")
    print("=" * 50)

    # Bước 2: Tiếp tục với state đã cập nhật
    print(f"\n\U0001f680 Step 2: Resuming with edit command...")
    print("=" * 50)
    
    result = graph.invoke(Command(resume=[{
                    "type": "edit",
                    "args": {
                        "args": {
                            "text": """
Kính gửi Quý khách hàng,

Chúng tôi xin thông báo hệ thống sẽ được bảo trì vào ngày 05/09/2025 từ 01:00 đến 03:00 (UTC).
Trong thời gian này, dịch vụ có thể tạm thời không khả dụng.

Mọi thắc mắc xin liên hệ: support@company.com hoặc hotline: 1900-xxxx

Trân trọng,
Ban Quản trị Hệ thống
                            """.strip()
                        }
                    }
                }]), config=config)
    
    print(f"\n\U0001f3af Final Result:")
    print(f"   \U0001f4ca Step count: {result.get('step_count', 'unknown')}")
    print(f"   ✅ Approved: {result.get('is_approved', False)}")
    print(f"   \U0001f4da History entries: {len(result.get('review_history', []))}")
    print("\n\U0001f4dd Final Text:")
    print("-" * 40)
    print(result.get('current_text', 'No text'))

if __name__ == "__main__":
    run_text_review_demo()
