package lifeos.application.usecase;

import java.util.UUID;
import lifeos.application.Change;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/**
 * Actualización parcial de un proyecto: solo se tocan los campos provistos.
 * {@code name} en null significa "no tocar" (el dominio no admite un nombre
 * vacío); {@code description} usa {@link Change} para poder limpiarse.
 */
public class UpdateProject {

    private final ProjectRepository projectRepo;

    public UpdateProject(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public Project execute(UUID projectId, String name, Change<String> description) {
        Project project = projectRepo.get(projectId)
                .orElseThrow(() -> new ProjectNotFoundException(projectId));

        if (name != null) {
            project.rename(name);
        }
        if (description.isSet()) {
            project.describe(description.value());
        }

        projectRepo.update(project);
        return project;
    }
}
