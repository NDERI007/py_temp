## 📝 Task Manager CLI

This is a beginner-friendly Python project where I built a simple command-line task manager.
It was done as practice while learning Python fundamentals (Week 1).

The app supports:

Adding tasks

Listing tasks

Marking tasks as complete

Deleting tasks

All tasks are saved to task.json.

## 🚶 Workflow

1. Setup

Created a main.py file.

Learned how to use sys.argv to handle command-line arguments.

Decided on basic commands: add, list, complete, delete.

2. Saving Data

Used the json module to store tasks in task.json.

Created helper functions:

load_tasks() → reads tasks from JSON

save_tasks(tasks) → writes tasks back to JSON

3. Add Task

Used " ".join(sys.argv[2:]) to allow multi-word tasks.

Tasks are saved with structure:

{ "task": "Buy milk", "done": false }

4. List Tasks

Displayed tasks with numbers and ✅/❌ depending on "done".

Learned about enumerate() for numbering.

5. Complete Task

User provides task number.

Converted to 0-based index (int(sys.argv[2]) - 1).

Updated "done": true.

6. Delete Task

Same indexing idea as complete.

Removed task using .pop(index).

## 🖥️ Usage

python main.py add "create task manager CLI"
python main.py list
python main.py complete 1
python main.py delete 1
