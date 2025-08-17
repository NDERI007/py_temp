import sys
import json, os

task = [{
    'task': 'learn python basics', 'done': True
},
{'task': 'Build task manager', 'done': False}
]

def load_tasks():
    if os.path.exists('task.json'):
      with open('task.json', 'r') as f:
       return json.load(f)
    else:
     return[]
        
def save_tasks(tasks):
    with open('task.json', 'w') as f:
     json.dump(tasks, f, indent=2)      

if len(sys.argv) > 1:
    command = sys.argv[1]

    if command == 'add':
     if len(sys.argv) < 3:
       print('⚠️ Please provide a task to add')
       sys.exit(1)
     task = ' '.join(sys.argv[2:]) 
     tasks = load_tasks()
     tasks.append({'task': task, 'done': False})
     save_tasks(tasks)
     print(f'✅ Added task {task}')

    elif command == 'list':
      #handle listing task
      tasks = load_tasks()
      if not tasks:
        print('📭 No task found')
      
      for i, t in enumerate(tasks, start=1):
        status = '✅' if t['done'] else '❌'
        print(f"{i}. {status} {t['task']}")
    
    elif command == 'complete':
      index = int(sys.argv[2]) -1
      tasks = load_tasks()

      if 0 <= index < len(tasks):
       tasks[index]['done'] = True
       save_tasks(tasks)
       print(f"🎉 Marked as done {tasks[index] ['task']}")
      else:
        print('❌ Invalid task number')

    elif command == 'delete':
      index = int(sys.argv[2]) -1 # user gives 1- based index
      tasks = load_tasks()

      if 0 <= index < len(tasks):
       removed = tasks.pop(index)
       save_tasks(tasks)
       print(f"🗑 Deleted task: {removed['task']}")
      else:
        print('❌ Invalid task number')
    else:
     print("Usage:")
     print("  add <task>       Add a new task")
     print("  list             List all tasks")
     print("  complete <num>   Mark a task as done")
     print("  delete <num>     Delete a task")
