package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/** Marca una tarea existente como completada. */
public class CompleteTask {

    private final TaskRepository taskRepo;

    public CompleteTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
        task.complete();
        taskRepo.update(task);
        return task;
    }
}
