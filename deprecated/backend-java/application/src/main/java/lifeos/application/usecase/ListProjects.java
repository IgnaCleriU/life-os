package lifeos.application.usecase;

import java.util.List;
import lifeos.application.port.ProjectFilter;
import lifeos.application.port.ProjectRepository;
import lifeos.domain.Project;

/** Lista proyectos vivos, opcionalmente filtrados. */
public class ListProjects {

    private final ProjectRepository projectRepo;

    public ListProjects(ProjectRepository projectRepo) {
        this.projectRepo = projectRepo;
    }

    public List<Project> execute(ProjectFilter filter) {
        return projectRepo.list(filter);
    }
}
