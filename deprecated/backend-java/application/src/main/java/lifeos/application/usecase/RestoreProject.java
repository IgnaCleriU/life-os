package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/**
 * Deshace el borrado lógico de un proyecto. Como el borrado no cascadea,
 * restaurar no tiene que reconstruir nada.
 */
public class RestoreProject {

    private final ProjectRepository projectRepo;

    public RestoreProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(UUID projectId) {
        Project project = projectRepo.get(projectId, true)
                .orElseThrow(() -> new ProjectNotFoundException(projectId));
        project.restore();
        projectRepo.update(project);
        return project;
    }
}
