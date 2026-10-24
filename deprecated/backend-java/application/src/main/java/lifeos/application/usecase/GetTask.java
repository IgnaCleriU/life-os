package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/** Devuelve una tarea existente por id; falla si no existe o está borrada. */
public class GetTask {

    private final TaskRepository taskRepo;

    public GetTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId) {
        return taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
    }
}
