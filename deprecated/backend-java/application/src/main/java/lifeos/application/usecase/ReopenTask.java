package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/** Vuelve una tarea existente a pendiente. */
public class ReopenTask {

    private final TaskRepository taskRepo;

    public ReopenTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
        task.reopen();
        taskRepo.update(task);
        return task;
    }
}
