package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.application.port.TaskRepository;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/**
 * Mueve una tarea a otro proyecto existente. Si la tarea o el destino no
 * existen, falla sin modificar nada.
 */
public class MoveTask {

    private final TaskRepository taskRepo;
    private final ProjectRepository projectRepo;

    public MoveTask(TaskRepository taskRepo, ProjectRepository projectRepo) {
        this.taskRepo = taskRepo;
        this.projectRepo = projectRepo;
    }

    public Task execute(UUID taskId, UUID projectId) {
        Task task = taskRepo.get(taskId).orElseThrow(() -> new TaskNotFoundException(taskId));
        if (projectRepo.get(projectId).isEmpty()) {
            throw new ProjectNotFoundException(projectId);
        }

        task.moveTo(projectId);
        taskRepo.update(task);
        return task;
    }
}
