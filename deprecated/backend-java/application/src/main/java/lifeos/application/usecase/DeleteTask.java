package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/** Borra lógicamente una tarea existente; restaurarla es un cambio de campo. */
public class DeleteTask {

    private final TaskRepository taskRepo;

    public DeleteTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
        task.delete();
        taskRepo.update(task);
        return task;
    }
}
