package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.application.port.TaskRepository;
import lifeos.domain.ProjectNotFoundException;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/**
 * Deshace el borrado lógico de una tarea.
 *
 * <p>Falla si el proyecto padre no existe o está borrado: {@code DeleteProject}
 * solo borra proyectos sin tareas vivas, así que restaurar una tarea ahí la
 * dejaría colgando de un proyecto invisible.
 */
public class RestoreTask {

    private final TaskRepository taskRepo;
    private final ProjectRepository projectRepo;

    public RestoreTask(TaskRepository taskRepo, ProjectRepository projectRepo) {
        this.taskRepo = taskRepo;
        this.projectRepo = projectRepo;
    }

    public Task execute(UUID taskId) {
        Task task = taskRepo.get(taskId, true).orElseThrow(() -> new TaskNotFoundException(taskId));
        if (projectRepo.get(task.projectId()).isEmpty()) {
            throw new ProjectNotFoundException(task.projectId());
        }

        task.restore();
        taskRepo.update(task);
        return task;
    }
}
