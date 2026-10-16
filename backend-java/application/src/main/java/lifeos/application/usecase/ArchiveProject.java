package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/** Marca un proyecto existente como archivado. */
public class ArchiveProject {

    private final ProjectRepository projectRepo;

    public ArchiveProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(UUID projectId) {
        Project project = projectRepo.get(projectId)
                .orElseThrow(() -> new ProjectNotFoundException(projectId));
        project.archive();
        projectRepo.update(project);
        return project;
    }
}
