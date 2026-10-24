package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/** Marca una tarea existente como en curso. */
public class StartTask {

    private final TaskRepository taskRepo;

    public StartTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
        task.start();
        taskRepo.update(task);
        return task;
    }
}
