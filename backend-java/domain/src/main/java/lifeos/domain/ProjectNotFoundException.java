package lifeos.domain;

import java.util.UUID;

/** No existe un proyecto con el id buscado. */
public class ProjectNotFoundException extends DomainException {

    private final UUID projectId;

    public ProjectNotFoundException(UUID projectId) {
        super("No existe el proyecto con id " + projectId);
        this.projectId = projectId;
    }

    public UUID projectId() {
        return projectId;
    }
}
