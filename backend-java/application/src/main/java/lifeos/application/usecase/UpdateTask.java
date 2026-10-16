package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/**
 * Actualización parcial de una tarea: solo se tocan los campos provistos. Las
 * invariantes (título no vacío) las valida el dominio.
 */
public class UpdateTask {

    private final TaskRepository taskRepo;

    public UpdateTask(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public Task execute(UUID taskId, TaskUpdate update) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));

        if (update.title() != null) {
            task.rename(update.title());
        }
        if (update.priority() != null) {
            task.changePriority(update.priority());
        }
        if (update.dueDate().isSet()) {
            task.reschedule(update.dueDate().value());
        }
        if (update.description().isSet()) {
            task.describe(update.description().value());
        }

        taskRepo.update(task);
        return task;
    }
}
