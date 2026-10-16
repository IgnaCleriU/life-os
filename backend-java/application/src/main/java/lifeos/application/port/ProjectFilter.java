package lifeos.application.port;

import java.util.List;
import lifeos.domain.ProjectStatus;

/**
 * Filtros de {@link ProjectRepository#list}: se combinan con AND y un campo en
 * null no restringe. {@code text} busca subcadena en el nombre, sin distinguir
 * mayúsculas.
 */
public record ProjectFilter(List<ProjectStatus> statuses, String text) {

    public ProjectFilter {
        statuses = statuses == null ? null : List.copyOf(statuses);
    }

    public static ProjectFilter all() {
        return new ProjectFilter(null, null);
    }

    public ProjectFilter withStatuses(List<ProjectStatus> statuses) {
        return new ProjectFilter(statuses, text);
    }

    public ProjectFilter matching(String text) {
        return new ProjectFilter(statuses, text);
    }
}
