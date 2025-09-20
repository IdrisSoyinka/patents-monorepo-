# Human-in-the-Loop với LangGraph Interrupt Pattern

## Tổng quan

File `human_validation.py` đã được cập nhật để sử dụng pattern **"Review and Edit State"** từ LangGraph với `interrupt()` function. Điều này cho phép workflow tạm dừng tự động và chờ input từ người dùng.

## Cách hoạt động

### 1. Interrupt Pattern

```python
from langgraph.types import interrupt

def human_validation_node(state: PatentSearchState) -> Dict[str, Any]:
    # Tạm dừng workflow và chờ input từ người dùng
    human_input = interrupt({
        "task": "Review and edit the generated keywords",
        "current_keywords": {...},
        "instruction": "Please provide your feedback..."
    })
    
    # Xử lý input và tiếp tục
    validated_keywords = _process_human_input(human_input, seed_keywords)
    return {"validated_keywords": validated_keywords, ...}
```

### 2. Workflow Execution

```python
from langgraph.types import Command

# Tạo graph với checkpointer (bắt buộc cho interrupt)
app = create_graph()

# Chạy workflow đến điểm interrupt
thread_config = {"configurable": {"thread_id": "unique_id"}}
result = app.invoke(initial_state, config=thread_config)

# Workflow tạm dừng tại human_validation_node
# Hiển thị thông tin cho người dùng và nhận phản hồi

# Tiếp tục với phản hồi của người dùng
final_result = app.invoke(
    Command(resume=user_response), 
    config=thread_config
)
```

## Các loại phản hồi được hỗ trợ

### 1. Approval (Phê duyệt)
```python
# String đơn giản
app.invoke(Command(resume="approve"), config=thread_config)
```

### 2. Edit (Chỉnh sửa)
```python
# Dictionary với keywords mới
edited_response = {
    "action": "edit",
    "keywords": {
        "problem_purpose": ["new_keyword1", "new_keyword2"],
        "object_system": ["new_system1", "new_system2"],
        "environment_field": ["new_field1", "new_field2"]
    }
}
app.invoke(Command(resume=edited_response), config=thread_config)
```

### 3. Rejection (Từ chối)
```python
# Từ chối keywords hiện tại
app.invoke(Command(resume="reject"), config=thread_config)
```

## Dữ liệu được hiển thị cho người dùng

Khi workflow tạm dừng, người dùng sẽ nhận được:

```json
{
    "task": "Review and edit the generated keywords for patent search",
    "instruction": "Detailed instructions on available actions...",
    "current_keywords": {
        "problem_purpose": ["keyword1", "keyword2"],
        "object_system": ["system1", "system2"], 
        "environment_field": ["field1", "field2"]
    },
    "formatted_display": "Human-readable format of keywords..."
}
```

## Ưu điểm của pattern mới

### 1. **Tự động tạm dừng/tiếp tục**
- Không cần quản lý state manually
- LangGraph tự động lưu và restore state
- Thread-safe execution

### 2. **Linh hoạt trong UI**
- Có thể integrate với bất kỳ UI framework nào
- Support cho web app, desktop app, CLI
- Real-time collaboration possible

### 3. **Error handling tốt hơn**
- Automatic fallback khi interrupt fails
- State được preserve khi có lỗi
- Graceful degradation

## Implementation trong UI

### Web Application
```javascript
// Frontend gọi API để start workflow
const response = await fetch('/api/start-workflow', {
    method: 'POST',
    body: JSON.stringify({
        patent_description: "...",
        thread_id: "unique_thread_id"
    })
});

// Workflow tạm dừng, hiển thị keywords cho user
const interruptData = await response.json();
showKeywordsForReview(interruptData.current_keywords);

// User submit phản hồi
const userResponse = getUserFeedback();
await fetch('/api/resume-workflow', {
    method: 'POST', 
    body: JSON.stringify({
        thread_id: "unique_thread_id",
        user_response: userResponse
    })
});
```

### Desktop Application
```python
import tkinter as tk
from langgraph.types import Command

class PatentSearchApp:
    def start_workflow(self):
        # Chạy workflow trong background thread
        result = self.app.invoke(self.initial_state, config=self.thread_config)
        
        # Hiển thị dialog cho user review
        self.show_keywords_dialog(result.interrupt_data)
    
    def on_user_response(self, user_input):
        # Resume workflow với user input
        final_result = self.app.invoke(
            Command(resume=user_input),
            config=self.thread_config
        )
        self.show_results(final_result)
```

## Testing

Sử dụng các helper functions cho testing:

```python
from src.patent_search_agent.nodes.human_validation import (
    simulate_human_approval,
    simulate_human_edit
)

# Test approval
state_with_approval = simulate_human_approval(test_state)

# Test edits
edited_keywords = {"problem_purpose": ["new_keyword"]}
state_with_edits = simulate_human_edit(test_state, edited_keywords)
```

## Lưu ý quan trọng

1. **Checkpointer bắt buộc**: Phải có checkpointer để interrupt hoạt động
2. **Thread ID unique**: Mỗi workflow session cần thread ID riêng
3. **Error handling**: Luôn có fallback khi interrupt fails
4. **Security**: Validate user input trước khi resume
5. **Timeout**: Consider timeout cho user response trong production

## Ví dụ hoàn chỉnh

Xem file `examples/human_in_loop_example.py` để có ví dụ chi tiết về cách sử dụng pattern mới.
