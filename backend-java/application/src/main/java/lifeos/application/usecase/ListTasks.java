package lifeos.application.usecase;

import java.util.List;
import lifeos.application.port.TaskFilter;
import lifeos.application.port.TaskRepository;
import lifeos.domain.Task;

/**
 * Lista tareas vivas, opcionalmente filtradas. Sin filtros devuelve las de
 * todos los proyectos, lo que alimenta las vistas de vencidas y la búsqueda.
 */
public class ListTasks {

    private final TaskRepository taskRepo;

    public ListTasks(TaskRepository taskRepo) {
        this.taskRepo = taskRepo;
    }

    public List<Task> execute(TaskFilter filter) {
        return taskRepo.list(filter);
    }
}
