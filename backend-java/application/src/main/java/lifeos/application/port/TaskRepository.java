package lifeos.application.port;

import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lifeos.domain.Task;
import lifeos.domain.TaskNotFoundException;

/**
 * Puerto de persistencia de Task.
 *
 * <p>Las tareas borradas ({@code deletedAt} no nulo) quedan fuera de todas las
 * lecturas salvo que se pida {@code includeDeleted}. Ese filtro es
 * responsabilidad de la implementación, no de quien llama: si viviera en los
 * casos de uso, un método nuevo del repositorio podría olvidarlo.
 */
public interface TaskRepository {

    /** Persiste una tarea nueva. */
    void add(Task task);

    /** Devuelve la tarea viva con ese id. */
    default Optional<Task> get(UUID taskId) {
        return get(taskId, false);
    }

    /**
     * Devuelve la tarea con ese id. {@code includeDeleted} existe solo para que
     * {@code RestoreTask} pueda alcanzar una tarea borrada.
     */
    Optional<Task> get(UUID taskId, boolean includeDeleted);

    /** Devuelve las tareas vivas que cumplen todos los filtros dados. */
    List<Task> list(TaskFilter filter);

    /** Persiste los cambios de una tarea existente; lanza {@link TaskNotFoundException} si ya no existe. */
    void update(Task task);
}
