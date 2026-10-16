package lifeos.domain;

import java.util.UUID;

/** No existe una tarea con el id buscado. */
public class TaskNotFoundException extends DomainException {

    private final UUID taskId;

    public TaskNotFoundException(UUID taskId) {
        super("No existe la tarea con id " + taskId);
        this.taskId = taskId;
    }

    public UUID taskId() {
        return taskId;
    }
}
