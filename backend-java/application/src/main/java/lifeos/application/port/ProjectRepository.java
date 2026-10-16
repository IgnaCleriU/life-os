package lifeos.application.port;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lifeos.domain.Project;

/**
 * Puerto de persistencia de Project.
 *
 * <p>Los proyectos borrados ({@code deletedAt} no nulo) quedan fuera de todas las
 * lecturas salvo que se pida {@code includeDeleted}, por el mismo motivo que en
 * {@link TaskRepository}.
 */
public interface ProjectRepository {

    /** Persiste un proyecto nuevo. */
    void add(Project project);

    /** Devuelve el proyecto vivo con ese id. */
    default Optional<Project> get(UUID projectId) {
        return get(projectId, false);
    }

    /**
     * Devuelve el proyecto con ese id. {@code includeDeleted} existe solo para
     * que {@code RestoreProject} pueda alcanzar un proyecto borrado; ningún
     * listado lo expone.
     */
    Optional<Project> get(UUID projectId, boolean includeDeleted);

    /** Devuelve los proyectos vivos que cumplen todos los filtros dados. */
    List<Project> list(ProjectFilter filter);

    /** Persiste los cambios de un proyecto existente. */
    void update(Project project);
}
