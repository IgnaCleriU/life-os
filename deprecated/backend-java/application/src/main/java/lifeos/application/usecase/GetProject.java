package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/** Devuelve un proyecto existente por id; falla si no existe o está borrado. */
public class GetProject {

    private final ProjectRepository projectRepo;

    public GetProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(UUID projectId) {
        return projectRepo.get(projectId).orElseThrow(() -> new ProjectNotFoundException(projectId));
    }
}
