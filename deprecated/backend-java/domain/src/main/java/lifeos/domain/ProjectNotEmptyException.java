package lifeos.domain;

import java.util.UUID;

/**
 * Se intenta borrar un proyecto que todavía tiene tareas vivas.
 *
 * <p>El borrado no cascadea: las tareas se mueven o se borran primero. Así
 * {@code RestoreProject} no necesita recordar qué tareas se llevó por delante.
 */
public class ProjectNotEmptyException extends DomainException {

    private final UUID projectId;

    public ProjectNotEmptyException(UUID projectId) {
        super("El proyecto con id " + projectId + " todavía tiene tareas");
        this.projectId = projectId;
    }

    public UUID projectId() {
        return projectId;
    }
}
