package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.application.port.TaskFilter;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotEmptyException;
import lifeos.domain.ProjectNotFoundException;

/**
 * Borra lógicamente un proyecto que ya no tiene tareas vivas.
 *
 * <p>El borrado <b>no cascadea</b>. Cascadear obligaría a {@code RestoreProject}
 * a recordar exactamente qué tareas se llevó por delante, y dejaría tareas
 * invisibles pero vivas si esa memoria se pierde. Mover o borrar las tareas
 * primero es explícito y reversible paso a paso.
 */
public class DeleteProject {

    private final ProjectRepository projectRepo;
    private final TaskRepository taskRepo;

    public DeleteProject(ProjectRepository projectRepo, TaskRepository taskRepo) {
        this.projectRepo = projectRepo;
        this.taskRepo = taskRepo;
    }

    public Project execute(UUID projectId) {
        Project project = projectRepo.get(projectId)
                .orElseThrow(() -> new ProjectNotFoundException(projectId));
        if (!taskRepo.list(TaskFilter.all().inProject(projectId)).isEmpty()) {
            throw new ProjectNotEmptyException(projectId);
        }

        project.delete();
        projectRepo.update(project);
        return project;
    }
}
