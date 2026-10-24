package lifeos.application.port;

import java.time.LocalDate;
import java.util.List;
import java.util.UUID;
import lifeos.domain.TaskStatus;

/**
 * Filtros de {@link TaskRepository#list}: se combinan con AND y un campo en null
 * no restringe. {@code dueBefore} es inclusivo y descarta las tareas sin fecha;
 * {@code text} busca subcadena en el título, sin distinguir mayúsculas.
 */
public record TaskFilter(UUID projectId, List<TaskStatus> statuses, LocalDate dueBefore, String text) {

    public TaskFilter {
        statuses = statuses == null ? null : List.copyOf(statuses);
    }

    public static TaskFilter all() {
        return new TaskFilter(null, null, null, null);
    }

    public TaskFilter inProject(UUID projectId) {
        return new TaskFilter(projectId, statuses, dueBefore, text);
    }

    public TaskFilter withStatuses(List<TaskStatus> statuses) {
        return new TaskFilter(projectId, statuses, dueBefore, text);
    }

    public TaskFilter dueOnOrBefore(LocalDate dueBefore) {
        return new TaskFilter(projectId, statuses, dueBefore, text);
    }

    public TaskFilter matching(String text) {
        return new TaskFilter(projectId, statuses, dueBefore, text);
    }
}
