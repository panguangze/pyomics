import sys
sys.path.extend(['/home/platform/pyomics_for_rails'])
from pyomics.core.exceptions import ModuleOutputNotExist, ModuleTaskDoesNotExist
from pyomics.data import models
import os
import json

@models.model_operation
def get_all_tasks_in_project(root_dir):
    task_info = {}
    projects = models.Project.select().where(models.Project.root_dir == root_dir)
    project = projects[len(projects) - 1]
    tasks = project.tasks
    for task in tasks:
        if task.module_label not in task_info:
            task_info[task.module_label] = []
        task_info[task.module_label].append({
            "task_id": task.name,
            "created_at": task.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "finished_at": task.finished_at.strftime('%Y-%m-%d %H:%M:%S') if task.finished_at else "not finished"
        })
    with open(os.path.join(root_dir, '.task_query.json'), 'w') as output:
        output.write(json.dumps(task_info))
if __name__ == "__main__":
    root_dir = sys.argv[1]
    get_all_tasks_in_project(root_dir)
