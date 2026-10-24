package lifeos.application.usecase;

import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;

/**
 * Crea un Project y lo persiste. La validación del nombre vive en el dominio:
 * si es inválido, {@link Project#create} lanza y no se persiste nada.
 */
public class CreateProject {

    private final ProjectRepository projectRepo;

    public CreateProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(String name, String description) {
        Project project = Project.create(name, description);
        projectRepo.add(project);
        return project;
    }
}
