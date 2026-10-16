package lifeos.application.fakes;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lifeos.application.port.TaskFilter;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;

/** {@link TaskRepository} en memoria para tests; mismo criterio que el de proyectos. */
public class InMemoryTaskRepository implements TaskRepository {

    private final Map<UUID, Task> tasks = new LinkedHashMap<>();

    @Override
    public void add(Task task) {
        tasks.put(task.id(), task);
    }

    @Override
    public Optional<Task> get(UUID taskId, boolean includeDeleted) {
        Task task = tasks.get(taskId);
        if (task == null || (task.isDeleted() && !includeDeleted)) {
            return Optional.empty();
        }
        return Optional.of(task);
    }

    @Override
    public List<Task> list(TaskFilter filter) {
        return tasks.values().stream()
                .filter(task -> !task.isDeleted())
                .filter(task -> filter.projectId() == null
                        || task.projectId().equals(filter.projectId()))
                .filter(task -> filter.statuses() == null
                        || filter.statuses().contains(task.status()))
                .filter(task -> filter.dueBefore() == null
                        || (task.dueDate() != null && !task.dueDate().isAfter(filter.dueBefore())))
                .filter(task -> filter.text() == null
                        || task.title().toLowerCase().contains(filter.text().toLowerCase()))
                .toList();
    }

    @Override
    public void update(Task task) {
        tasks.put(task.id(), task);
    }
}
