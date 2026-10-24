package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/** Vuelve a poner un proyecto existente como activo. */
public class ActivateProject {

    private final ProjectRepository projectRepo;

    public ActivateProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(UUID projectId) {
        Project project = projectRepo.get(projectId)
                .orElseThrow(() -> new ProjectNotFoundException(projectId));
        project.activate();
        projectRepo.update(project);
        return project;
    }
}
