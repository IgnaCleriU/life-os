package lifeos.application.fakes;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lifeos.application.port.ProjectFilter;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;
import lifeos.domain.ProjectNotFoundException;

/**
 * {@link ProjectRepository} en memoria para tests.
 *
 * <p>Guarda las entidades por id sin copiarlas y replica el filtrado de borrados
 * lógicos del repositorio SQLite: si el fake mostrara entidades borradas, cada
 * test de caso de uso verificaría un contrato que la implementación real no cumple.
 */
public class InMemoryProjectRepository implements ProjectRepository {

    private final Map<UUID, Project> projects = new LinkedHashMap<>();

    @Override
    public void add(Project project) {
        projects.put(project.id(), project);
    }

    @Override
    public Optional<Project> get(UUID projectId, boolean includeDeleted) {
        Project project = projects.get(projectId);
        if (project == null || (project.isDeleted() && !includeDeleted)) {
            return Optional.empty();
        }
        return Optional.of(project);
    }

    @Override
    public List<Project> list(ProjectFilter filter) {
        return projects.values().stream()
                .filter(project -> !project.isDeleted())
                .filter(project -> filter.statuses() == null
                        || filter.statuses().contains(project.status()))
                .filter(project -> filter.text() == null
                        || project.name().toLowerCase().contains(filter.text().toLowerCase()))
                .toList();
    }

    @Override
    public void update(Project project) {
        if (!projects.containsKey(project.id())) {
            throw new ProjectNotFoundException(project.id());
        }
        projects.put(project.id(), project);
    }
}
