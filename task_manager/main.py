import sys
import json, os

task = [{
    'task': 'learn python basics', 'done': True
},
{'task': 'Build task manager', 'done': False}
]

print('First argument (Script Name)', sys.argv[0])

if len(sys.argv) > 1:
    command = sys.argv[1]

    if command == 'add':
     task = sys.argv[2]
     print('Added task:', task)

     def load_tasks():
        if os.path.exists('task.json'):
         with open('task.json', 'r') as f:
           return json.load(f)
        else:
          return[]
        
    def save_tasks(tasks):
        with open('task.json', 'w') as f:
         json.dump(tasks, f, indent=2)